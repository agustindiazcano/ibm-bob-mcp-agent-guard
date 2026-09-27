"""
Phase 18 checks for scripts/verify.py (multi-agent swarm groundwork).

    phase18-s3 — lane sandbox + owned-path write guard (Step S3): an owned
                 write succeeds; every other path (a source file, another
                 lane's file, tests/conftest.py, a ".." escape, an absolute
                 path into the real repo's tests/) raises SourceEditRejected;
                 the critic toolset has no write tool at all; the sandbox is
                 gone after both a normal exit and an exception inside the
                 context manager; the real demo-repo is byte-for-byte
                 unchanged throughout.

    phase18-s4 — plan/blackboard/Verifier/lane state machine/thread pool
                 (Step S4): a ScriptedProvider on a temp demo-repo copy,
                 run_lanes(workers=4), all 4 lanes ACCEPTED round 1 with
                 newly_killed > 0 and regressed == [], timeline.jsonl shows
                 overlapping lane spans, every recorded lane sandbox is gone
                 afterward, the real tests/ manifest is unchanged, and
                 workers=1 vs workers=4 give identical verify-1.json records.
                 Also: a writer that only ever produces a failing test
                 exhausts both rounds and ends FAILED, and a writer whose
                 script raises is caught and reported FAILED without
                 crashing the run.

Each check runs its script in a fresh interpreter (sys.executable), same as
verify.py and verify_phase17.py.
"""

from __future__ import annotations

import subprocess
import sys


def _run_script(script: str, timeout: int) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout + proc.stderr


_PHASE18_S3_SCRIPT = r"""
import hashlib
from pathlib import Path
from repoguard_engine.swarm.sandbox import lane_sandbox
from repoguard_engine.swarm.guard import writer_toolset, critic_toolset
from repoguard_engine.watson_agent.tools import SourceEditRejected

def file_hashes(root):
    out = {}
    for p in sorted(Path(root).rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and '.git' not in p.parts and 'repoguard-out' not in p.parts:
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out

real_repo = Path('demo-repo').resolve()
before = file_hashes(real_repo)
owned = 'tests/test_lane_probe.py'
sandbox_seen = None

with lane_sandbox(real_repo, 'lane-0') as sandbox:
    sandbox_seen = sandbox
    schemas, registry = writer_toolset(sandbox, owned)
    assert {s['function']['name'] for s in schemas} == {'read_source_file', 'write_test_file', 'run_tests'}

    write = registry['write_test_file']
    result = write(repo_path=str(sandbox), file_path=owned, content='def test_x():\n    assert True\n')
    assert result['ok'] is True, result
    print('OK: owned write succeeded')

    rejected = {}
    for bad_path in (
        'shop/cart.py',
        'tests/test_another_lane.py',
        'tests/conftest.py',
        'tests/../shop/cart.py',
        '../x.py',
    ):
        try:
            write(repo_path=str(sandbox), file_path=bad_path, content='x = 1\n')
            rejected[bad_path] = False
        except SourceEditRejected:
            rejected[bad_path] = True
    assert all(rejected.values()), rejected
    print(f'OK: {len(rejected)} out-of-scope paths all raised SourceEditRejected')

    real_target = str(real_repo / 'tests' / 'test_should_never_exist.py')
    try:
        write(repo_path=str(sandbox), file_path=real_target, content='x = 1\n')
        raise AssertionError('an absolute path into the real repo tests/ was accepted')
    except SourceEditRejected:
        pass
    assert not (real_repo / 'tests' / 'test_should_never_exist.py').exists()
    print('OK: absolute path into the real repo tests/ raised SourceEditRejected')

    c_schemas, c_registry = critic_toolset()
    assert {s['function']['name'] for s in c_schemas} == {'read_source_file', 'run_tests'}
    assert 'write_test_file' not in c_registry
    print('OK: critic toolset has no write tool')

assert not sandbox_seen.exists(), 'sandbox still exists after a normal exit'
print('OK: sandbox gone after normal exit')

leaked = None
try:
    with lane_sandbox(real_repo, 'lane-1') as sandbox2:
        leaked = sandbox2
        raise RuntimeError('boom')
except RuntimeError:
    pass
assert leaked is not None and not leaked.exists(), 'sandbox not cleaned up after an exception'
print('OK: sandbox gone after an exception inside the context manager')

after = file_hashes(real_repo)
assert before == after, 'the real demo-repo changed during the lane sandbox test'
print('OK: real demo-repo byte-for-byte unchanged throughout')
"""


def check_phase18_s3() -> bool:
    """Lane sandbox + owned-path write guard: owned write succeeds, every
    out-of-scope path (source, another lane's file, conftest.py, a ".."
    escape, an absolute path into the real repo) is rejected, the critic
    has no write tool, sandboxes are cleaned up on both a normal exit and
    an exception, and the real demo-repo never changes."""
    print("=== Phase 18 S3: lane sandbox + owned-path write guard ===")
    rc, out = _run_script(_PHASE18_S3_SCRIPT, timeout=120)
    ok = rc == 0
    print(out.rstrip() if ok else out[-3000:])
    print(f"  sandbox + write guard -> {'PASS' if ok else 'FAIL'}")
    return ok


_PHASE18_S4_SCRIPT = r"""
import hashlib, json, shutil, tempfile
from contextlib import contextmanager
from pathlib import Path

import repoguard_engine.swarm.runner as runner_mod
from repoguard_engine.pipeline import run_pipeline
from repoguard_engine.swarm.blackboard import read_stage, run_dir
from repoguard_engine.swarm.lane import owned_test_path, run_lane
from repoguard_engine.swarm.plan import build_plan
from repoguard_engine.swarm.sandbox import lane_sandbox as real_lane_sandbox
from repoguard_engine.testing import ScriptedProvider, reference_writer

demo = Path('demo-repo').resolve()


def tree_hash(root):
    h = hashlib.sha256()
    for p in sorted(root.rglob('*')):
        if p.is_file() and not any(s in p.parts for s in ('__pycache__', 'repoguard-out', '.git', '.pytest_cache')):
            h.update(str(p.relative_to(root)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def tests_manifest(repo):
    manifest = {}
    root = repo / 'tests'
    for p in sorted(root.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:
            manifest[p.relative_to(repo).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return manifest


before = tree_hash(demo)
created_sandboxes = []


@contextmanager
def spying_lane_sandbox(repo, lane_id):
    with real_lane_sandbox(repo, lane_id) as sandbox:
        created_sandboxes.append(sandbox)
        yield sandbox


runner_mod.lane_sandbox = spying_lane_sandbox

with tempfile.TemporaryDirectory(prefix='repoguard-s4-') as tmp:
    work = Path(tmp) / 'demo-repo'
    shutil.copytree(
        demo, work,
        ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache', 'repoguard-out', 'watson-evidence', '.git'),
    )

    baseline = run_pipeline(str(work), include_mutation=True, include_endpoints=False, persist=False)
    assert (round(baseline.dashboard['coverage']['percent'], 1), baseline.mutation.killed, baseline.mutation.total) == (
        60.3, 16, 79,
    ), 'baseline drifted from AGENTS.md Section 7'

    plan = build_plan(baseline)
    modules = [lane.module for lane in plan.lanes]
    assert set(modules) == {'shop/api.py', 'shop/cart.py', 'shop/inventory.py', 'shop/pricing.py'}, modules
    manifest_before = tests_manifest(work)

    def provider_factory():
        return ScriptedProvider(
            {'writer': reference_writer('docs/expected-after-tests', target_for=lambda src: owned_test_path(src))}
        )

    result4 = runner_mod.run_lanes(work, plan, provider_factory, run_id='verify-w4', workers=4, rounds=2, mutation_workers=4)
    assert len(created_sandboxes) >= len(plan.lanes), (len(created_sandboxes), len(plan.lanes))
    assert not any(p.exists() for p in created_sandboxes), [p for p in created_sandboxes if p.exists()]
    print(f'OK: all {len(created_sandboxes)} recorded lane sandboxes gone after the run')

    for outcome in result4.lanes:
        assert outcome.status == 'ACCEPTED', (outcome.module, outcome.status, outcome.error)
        assert outcome.round == 1, (outcome.module, outcome.round)
        assert outcome.newly_killed, outcome.module
    print(f'OK: all {len(result4.lanes)} lanes ACCEPTED round 1 with newly_killed > 0')

    rd4 = run_dir(work, 'verify-w4')
    for module in modules:
        vr = read_stage(rd4, module, 'verify', 1)
        assert vr is not None and vr['regressed'] == [], (module, vr)
    print('OK: regressed == [] for every lane')

    lines = [json.loads(x) for x in (rd4 / 'timeline.jsonl').read_text(encoding='utf-8').splitlines()]
    spans = {}
    for ev in lines:
        if ev['agent'] == 'runner' and ev['kind'] in ('lane_start', 'lane_end'):
            spans.setdefault(ev['lane'], {})[ev['kind']] = ev['ts']
    intervals = [(v['lane_start'], v['lane_end']) for v in spans.values() if 'lane_start' in v and 'lane_end' in v]
    overlaps = sum(
        1
        for i in range(len(intervals))
        for j in range(i + 1, len(intervals))
        if intervals[i][0] < intervals[j][1] and intervals[j][0] < intervals[i][1]
    )
    assert len(intervals) >= 2 and overlaps >= 1, (intervals, overlaps)
    print(f'OK: timeline.jsonl shows {len(intervals)} lanes, {overlaps} overlapping pair(s)')

    assert tests_manifest(work) == manifest_before, 'the real tests/ dir changed during the run'
    print('OK: real tests/ manifest unchanged')

    created_sandboxes.clear()
    result1 = runner_mod.run_lanes(work, plan, provider_factory, run_id='verify-w1', workers=1, rounds=2, mutation_workers=4)
    rd1 = run_dir(work, 'verify-w1')
    for module in modules:
        v4 = read_stage(rd4, module, 'verify', 1)
        v1 = read_stage(rd1, module, 'verify', 1)
        for key in ('suite_passed', 'newly_killed', 'still_alive', 'regressed', 'newly_covered', 'total_mutants'):
            assert v4[key] == v1[key], (module, key, v4[key], v1[key])
    print('OK: workers=1 and workers=4 give identical verify-1.json records')

    # A writer that only ever produces a failing test: exhausts both rounds, ends FAILED.
    failing_calls = {'n': 0}

    def failing_script(_role, _messages):
        failing_calls['n'] += 1
        if failing_calls['n'] % 2 == 1:
            return {
                'role': 'assistant', 'content': None,
                'tool_calls': [{
                    'type': 'function',
                    'function': {
                        'name': 'write_test_file',
                        'arguments': json.dumps({
                            'file_path': owned_test_path('shop/cart.py'),
                            'content': 'def test_always_fails():\n    assert False\n',
                        }),
                    },
                }],
            }
        return {'role': 'assistant', 'content': 'gave up'}

    cart_plan = next(lane for lane in plan.lanes if lane.module == 'shop/cart.py')
    rd_fail = run_dir(work, 'verify-failed')
    from repoguard_engine.swarm.blackboard import Timeline
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=1) as pool, real_lane_sandbox(work, 'verify-fail-lane') as sandbox:
        outcome = run_lane(
            sandbox, cart_plan, lambda: ScriptedProvider({'writer': failing_script}), rd_fail, Timeline(rd_fail),
            pool, rounds=2, mutation_workers=1, lane_index=0,
        )
    assert outcome.status == 'FAILED', outcome
    assert not outcome.suite_passed, outcome
    print('OK: a writer that only produces a failing test ends FAILED after exhausting both rounds')

    # A writer whose script raises: caught, reported FAILED, doesn't crash the run.
    def raising_script(_role, _messages):
        raise RuntimeError('scripted boom')

    rd_boom = run_dir(work, 'verify-boom')
    with ThreadPoolExecutor(max_workers=1) as pool, real_lane_sandbox(work, 'verify-boom-lane') as sandbox:
        outcome = run_lane(
            sandbox, cart_plan, lambda: ScriptedProvider({'writer': raising_script}), rd_boom, Timeline(rd_boom),
            pool, rounds=2, mutation_workers=1, lane_index=0,
        )
    assert outcome.status == 'FAILED', outcome
    assert outcome.error and 'scripted boom' in outcome.error, outcome
    print('OK: a writer script that raises is caught and reported FAILED, not propagated')

assert tree_hash(demo) == before, 'the real demo-repo changed during the S4 verify run'
print('OK: real demo-repo byte-for-byte unchanged throughout')
"""


def check_phase18_s4() -> bool:
    """Lane state machine + thread pool + blackboard (Step S4): a
    ScriptedProvider on a temp demo-repo copy, run_lanes(workers=4) puts all
    4 lanes ACCEPTED at round 1 with real kills and no regressions,
    timeline.jsonl shows overlapping lane spans, every recorded sandbox is
    gone afterward, the real tests/ dir is untouched, and workers=1/workers=4
    agree exactly. A writer that only ever fails and a writer whose script
    raises both end the lane FAILED without taking down the run."""
    print("=== Phase 18 S4: lane state machine, thread pool, blackboard ===")
    rc, out = _run_script(_PHASE18_S4_SCRIPT, timeout=3600)
    ok = rc == 0
    print(out.rstrip() if ok else out[-4000:])
    print(f"  lane state machine + thread pool -> {'PASS' if ok else 'FAIL'}")
    return ok
