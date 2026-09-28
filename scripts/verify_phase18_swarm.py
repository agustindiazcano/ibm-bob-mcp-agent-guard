"""
Phase 18 swarm checks for scripts/verify.py (Steps S5-S7, docs/MULTI_AGENT_SWARM.md
Section 14). Split from verify_phase18.py to keep both files under ~600 lines.

    phase18-s5 — read-only critic with a JSON verdict: NEEDS_WORK then
                 APPROVED -> exactly 2 writer stages and the round-2 prompt
                 carries the round-1 weakness; NEEDS_WORK twice -> still 2
                 rounds (cap); garbage -> one re-ask, UNPARSEABLE, 1 round;
                 the critic only ever sees {read_source_file, run_tests}; a
                 critic calling write_test_file gets "no such tool" and the
                 lane file's sha256 is unchanged.

    phase18-s6 — fan-in, Gate rollback, CLI flag: two lane files that each
                 pass alone but fail together -> the later-sorted one is
                 REJECTED_AT_FANIN and the merged suite is green; tests/
                 changed after planning -> FanInAborted, nothing written; a
                 Gate that raises -> fan-in rolled back, an overwritten file
                 restored byte for byte, gate.json records the error;
                 `repoguard fix --help` shows --swarm.

    phase18-s7 — credential-free end to end: run_swarm with reference_writer
                 + an APPROVED critic on a temp demo-repo copy reaches the
                 documented "after" numbers (71 passed, coverage 100.0,
                 mutation 89.87 = 71/79), all 4 lanes ACCEPTED, lanes overlap
                 in the timeline, no sandbox left, and workers=1 gives the
                 identical Gate.

Every check runs on temp copies; the real demo-repo must stay byte-identical.
"""

from __future__ import annotations

import subprocess
import sys


def _run_script(script: str, timeout: int) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-c", _COMMON + script], capture_output=True, text=True, timeout=timeout, check=False)
    return proc.returncode, proc.stdout + proc.stderr


_COMMON = r"""
import hashlib, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

demo = Path('demo-repo').resolve()
REFERENCE = 'docs/expected-after-tests'


def tree_hash(root):
    h = hashlib.sha256()
    for p in sorted(root.rglob('*')):
        if p.is_file() and not any(s in p.parts for s in ('__pycache__', 'repoguard-out', '.git', '.pytest_cache')):
            h.update(str(p.relative_to(root)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def copy_demo(tmp):
    work = Path(tmp) / 'demo-repo'
    shutil.copytree(
        demo, work,
        ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache', 'repoguard-out', 'watson-evidence', '.git'),
    )
    return work


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


demo_before = tree_hash(demo)
"""


_PHASE18_S5_SCRIPT = r"""
from concurrent.futures import ThreadPoolExecutor

from repoguard_engine.pipeline import run_pipeline
from repoguard_engine.swarm import blackboard
from repoguard_engine.swarm.critic import UNPARSEABLE, run_critic
from repoguard_engine.swarm.guard import critic_toolset
from repoguard_engine.swarm.lane import owned_test_path, run_lane
from repoguard_engine.swarm.plan import build_plan
from repoguard_engine.swarm.sandbox import lane_sandbox
from repoguard_engine.testing import ScriptedProvider, json_critic, reference_writer

MODULE = 'shop/pricing.py'
OWNED = owned_test_path(MODULE)
CRITIC_TOOLS = {'read_source_file', 'run_tests'}


def stage_starts(provider, role):
    return [
        c for c in provider.calls
        if c.role == role and not any(m.get('role') == 'assistant' for m in c.messages)
    ]


with tempfile.TemporaryDirectory(prefix='repoguard-s5-') as tmp:
    work = copy_demo(tmp)
    baseline = run_pipeline(str(work), include_mutation=True, include_endpoints=False, persist=False)
    assert (baseline.mutation.killed, baseline.mutation.total) == (16, 79), 'baseline drifted from AGENTS.md Section 7'
    lane_plan = next(lane for lane in build_plan(baseline).lanes if lane.module == MODULE)

    def run(tag, critic_script, rounds=2):
        provider = ScriptedProvider({
            'writer': reference_writer(REFERENCE, target_for=owned_test_path),
            'critic': critic_script,
        })
        rd = blackboard.run_dir(work, f'verify-s5-{tag}')
        with ThreadPoolExecutor(max_workers=2) as pool, lane_sandbox(work, f's5-{tag}') as sandbox:
            outcome = run_lane(
                sandbox, lane_plan, lambda _role: provider, rd, blackboard.Timeline(rd), pool,
                rounds=rounds, mutation_workers=2, lane_index=0,
            )
        return outcome, provider, rd

    outcome, provider, rd = run('revise', json_critic('NEEDS_WORK', 'APPROVED', weakness='boundary n+1 never asserted'))
    writers = stage_starts(provider, 'writer')
    assert len(writers) == 2, len(writers)
    assert 'boundary n+1 never asserted' in writers[1].messages[1]['content'], writers[1].messages[1]['content']
    assert 'boundary n+1 never asserted' not in writers[0].messages[1]['content']
    assert blackboard.read_stage(rd, MODULE, 'critic', 1)['verdict'] == 'NEEDS_WORK'
    assert blackboard.read_stage(rd, MODULE, 'critic', 2)['verdict'] == 'APPROVED'
    assert outcome.status == 'ACCEPTED' and outcome.rounds_run == 2, outcome
    print('OK: NEEDS_WORK then APPROVED -> exactly 2 writer stages, round-2 prompt carries the weakness')

    for call in provider.calls:
        if call.role == 'critic':
            assert set(call.tools) == CRITIC_TOOLS, call.tools
    assert {s['function']['name'] for s in critic_toolset()[0]} == CRITIC_TOOLS
    print('OK: the critic only ever saw {read_source_file, run_tests}')

    outcome, provider, rd = run('cap', json_critic('NEEDS_WORK'))
    assert len(stage_starts(provider, 'writer')) == 2 and outcome.rounds_run == 2, outcome
    assert outcome.status == 'ACCEPTED', outcome
    print('OK: NEEDS_WORK twice -> still exactly 2 rounds (cap respected), status from the Verifier')

    outcome, provider, rd = run('garbage', json_critic('I think these tests look fine overall.'))
    assert outcome.verdict == UNPARSEABLE, outcome.verdict
    assert outcome.rounds_run == 1 and len(stage_starts(provider, 'writer')) == 1, outcome
    assert len(stage_starts(provider, 'critic')) == 2, 'expected exactly one JSON-only re-ask'
    assert outcome.status == 'ACCEPTED', outcome
    print('OK: unparseable critic -> one re-ask, UNPARSEABLE, 1 round, still ACCEPTED on the measurement')

    def writing_critic(_role, messages):
        if not any(m.get('role') == 'assistant' for m in messages):
            return {
                'role': 'assistant', 'content': None,
                'tool_calls': [{'type': 'function', 'function': {
                    'name': 'write_test_file',
                    'arguments': json.dumps({'file_path': OWNED, 'content': 'def test_x():\n    assert False\n'}),
                }}],
            }
        return {'role': 'assistant', 'content': json.dumps({'verdict': 'APPROVED', 'weaknesses': [], 'blocker': None})}

    with lane_sandbox(work, 's5-write') as sandbox:
        target = sandbox / OWNED
        target.write_text((Path(REFERENCE) / 'test_pricing_complete.py').read_text(encoding='utf-8'), encoding='utf-8')
        before = sha(target)
        provider = ScriptedProvider({'critic': writing_critic})
        verdict = run_critic(sandbox, MODULE, OWNED, provider, [])
        tool_msgs = [m for m in provider.calls[-1].messages if m.get('role') == 'tool']
        assert tool_msgs and 'no such tool' in tool_msgs[0]['content'], tool_msgs
        assert sha(target) == before, 'the critic changed the lane file'
        assert verdict.verdict == 'APPROVED', verdict
    print('OK: a critic calling write_test_file gets "no such tool"; lane file sha256 unchanged')

assert tree_hash(demo) == demo_before, 'the real demo-repo changed during the S5 verify run'
print('OK: real demo-repo byte-for-byte unchanged throughout')
"""


_PHASE18_S6_SCRIPT = r"""
from click.testing import CliRunner

import repoguard_engine.swarm.run as run_mod
from repoguard_engine.cli import main as cli_main
from repoguard_engine.swarm import blackboard
from repoguard_engine.swarm.fanin import FanInAborted, fan_in, rollback
from repoguard_engine.swarm.lane import LaneOutcome, owned_test_path
from repoguard_engine.swarm.plan import LanePlan, Plan, _tests_manifest
from repoguard_engine.swarm.runner import RunResult
from repoguard_engine.watson_agent.tools import run_tests

A, B = 'shop/api.py', 'shop/cart.py'
# Collection imports every test module before any test runs, so A's import-time
# side effect breaks B in any order -- but each file passes alone.
A_CONTENT = "import os\nos.environ['REPOGUARD_S6_CONFLICT'] = '1'\n\n\ndef test_a_alone():\n    assert True\n"
B_CONTENT = "import os\n\n\ndef test_b_needs_clean_env():\n    assert 'REPOGUARD_S6_CONFLICT' not in os.environ\n"


def accepted(rd, module, content):
    return LaneOutcome(module=module, status='ACCEPTED', round=1, suite_passed=True,
                       test_sha256=blackboard.write_final_test(rd, module, content))


with tempfile.TemporaryDirectory(prefix='repoguard-s6-') as tmp:
    work = copy_demo(tmp)
    manifest0 = _tests_manifest(work, 'tests')

    # 1. Runtime conflict between two lanes -> the later-sorted one is dropped.
    rd = blackboard.run_dir(work, 'verify-s6-conflict')
    plan = Plan(lanes=[], tests_manifest=manifest0)
    result = fan_in(work, plan, [accepted(rd, B, B_CONTENT), accepted(rd, A, A_CONTENT)], rd)
    assert result.merged == [A], result.merged
    assert B in result.rejected and owned_test_path(A) in result.rejected[B], result.rejected
    assert set(_tests_manifest(work, 'tests')) == set(manifest0) | {owned_test_path(A)}
    assert run_tests(repo_path=str(work))['passed'], 'merged suite is red'
    print(f'OK: conflicting lane {B} REJECTED_AT_FANIN, merged suite green, only {owned_test_path(A)} added')
    rollback(work, result)
    assert _tests_manifest(work, 'tests') == manifest0
    print('OK: rollback removes an added file')

    # 2. tests/ changed after planning -> abort, nothing written.
    rd = blackboard.run_dir(work, 'verify-s6-abort')
    outcomes = [accepted(rd, A, A_CONTENT)]
    edited = work / 'tests' / 'test_cart.py'
    original = edited.read_bytes()
    edited.write_bytes(original + b'\n# edited under a running swarm\n')
    changed = _tests_manifest(work, 'tests')
    try:
        fan_in(work, plan, outcomes, rd)
        raise AssertionError('fan_in merged into a tests/ that changed since planning')
    except FanInAborted:
        pass
    assert _tests_manifest(work, 'tests') == changed, 'fan_in wrote despite aborting'
    edited.write_bytes(original)
    print('OK: tests/ changed after planning -> FanInAborted, nothing written')

    # 3. The Gate raises -> fan-in rolled back, an overwritten file restored exactly.
    stale = work / owned_test_path(A)
    stale.write_text('def test_from_an_earlier_swarm():\n    assert True\n', encoding='utf-8')
    stale_bytes = stale.read_bytes()
    manifest_gate = _tests_manifest(work, 'tests')
    calls = {'n': 0}

    class FakeBaseline:
        dashboard = {'note': 'faked for phase18-s6'}

    def fake_measure(_repo, _threshold, _workers):
        calls['n'] += 1
        if calls['n'] == 1:
            return FakeBaseline()
        raise RuntimeError('forced Gate failure')

    def fake_run_lanes(repo, _plan, _factory, *, run_id, **_kw):
        return RunResult(run_id=run_id, lanes=[accepted(blackboard.run_dir(Path(repo), run_id), A, "def test_new():\n    assert True\n")])

    run_mod._measure = fake_measure
    run_mod.build_plan = lambda _b: Plan(lanes=[LanePlan(module=A, survivors=1, risk=1.0)], tests_manifest=manifest_gate)
    run_mod.run_lanes = fake_run_lanes
    res = run_mod.run_swarm(work, provider_factory=lambda _role: None, run_id='verify-s6-gate', mutation_workers=1)
    assert res.error and 'forced Gate failure' in res.error, res.error
    assert not res.passed_gate and res.status == 'error', (res.passed_gate, res.status)
    assert _tests_manifest(work, 'tests') == manifest_gate, 'rollback left tests/ changed'
    assert stale.read_bytes() == stale_bytes, 'overwritten file not restored byte for byte'
    gate = json.loads((blackboard.run_dir(work, 'verify-s6-gate') / 'gate.json').read_text(encoding='utf-8'))
    assert 'forced Gate failure' in json.dumps(gate), gate
    assert res.evidence_path and Path(res.evidence_path).is_file()
    print('OK: Gate raised -> fan-in rolled back, overwritten file restored, gate.json records the error')

help_out = CliRunner().invoke(cli_main, ['fix', '--help']).output
for flag in ('--swarm', '--workers', '--rounds', '--mutation-workers'):
    assert flag in help_out, flag
print('OK: `repoguard fix --help` shows --swarm, --workers, --rounds, --mutation-workers')

assert tree_hash(demo) == demo_before, 'the real demo-repo changed during the S6 verify run'
print('OK: real demo-repo byte-for-byte unchanged throughout')
"""


_PHASE18_S7_SCRIPT = r"""
from contextlib import contextmanager

import repoguard_engine.swarm.fanin as fanin_mod
import repoguard_engine.swarm.runner as runner_mod
from repoguard_engine.core import pytest_env
from repoguard_engine.swarm import run_swarm
from repoguard_engine.swarm.lane import owned_test_path
from repoguard_engine.swarm.sandbox import lane_sandbox as real_lane_sandbox
from repoguard_engine.testing import ScriptedProvider, json_critic, reference_writer

created = []


@contextmanager
def spying_lane_sandbox(repo, lane_id):
    with real_lane_sandbox(repo, lane_id) as sandbox:
        created.append(sandbox)
        yield sandbox


runner_mod.lane_sandbox = spying_lane_sandbox
fanin_mod.lane_sandbox = spying_lane_sandbox


def factory(_role):
    return ScriptedProvider({
        'writer': reference_writer(REFERENCE, target_for=owned_test_path),
        'critic': json_critic('APPROVED'),
    })


def swarm_once(workers):
    with tempfile.TemporaryDirectory(prefix=f'repoguard-s7-w{workers}-') as tmp:
        work = copy_demo(tmp)
        res = run_swarm(work, provider_factory=factory, workers=workers, rounds=2, mutation_workers=4,
                        run_id=f'verify-s7-w{workers}')
        # No -q: demo-repo's pytest.ini already adds one, and -qq drops the 'N passed' line.
        proc = subprocess.run(
            [sys.executable, '-m', 'pytest', '-p', 'no:cacheprovider'],
            cwd=work, env=pytest_env(), capture_output=True, text=True, timeout=600, check=False,
        )
        match = re.search(r'(\d+) passed', proc.stdout)
        passed = int(match.group(1)) if match else -1
        timeline = [json.loads(x) for x in
                    (work / 'repoguard-out' / 'swarm' / res.run_id / 'timeline.jsonl').read_text(encoding='utf-8').splitlines()]
        return res, passed, proc.returncode, timeline


res4, passed4, rc4, timeline4 = swarm_once(4)
assert res4.error is None, res4.error
assert res4.status == 'accepted' and res4.passed_gate, (res4.status, res4.gate)
assert [o.status for o in res4.lanes] == ['ACCEPTED'] * 4, [(o.module, o.status, o.error) for o in res4.lanes]
after = res4.gate['after']
assert rc4 == 0 and passed4 == 71, (rc4, passed4)
assert after['coverage'] == 100.0, after['coverage']
assert (after['killed'], after['total'], round(after['mutation_score'], 2)) == (71, 79, 89.87), after
print(f"OK: workers=4 Gate: {passed4} passed, coverage {after['coverage']}, "
      f"mutation {round(after['mutation_score'], 2)} ({after['killed']}/{after['total']}), all 4 lanes ACCEPTED")

spans = {}
for ev in timeline4:
    if ev['agent'] == 'runner' and ev['kind'] in ('lane_start', 'lane_end'):
        spans.setdefault(ev['lane'], {})[ev['kind']] = ev['ts']
intervals = [(v['lane_start'], v['lane_end']) for v in spans.values() if len(v) == 2]
overlaps = sum(1 for i in range(len(intervals)) for j in range(i + 1, len(intervals))
               if intervals[i][0] < intervals[j][1] and intervals[j][0] < intervals[i][1])
assert len(intervals) == 4 and overlaps >= 1, (intervals, overlaps)
print(f'OK: timeline shows 4 lanes, {overlaps} overlapping pair(s)')

res1, passed1, rc1, _ = swarm_once(1)
assert res1.status == 'accepted' and passed1 == passed4, (res1.status, passed1)
for key in ('coverage', 'mutation_score', 'killed', 'total', 'surviving'):
    assert res1.gate['after'][key] == after[key], (key, res1.gate['after'][key], after[key])
print(f"OK: workers=1 gives the identical Gate and the same {len(after['surviving'])} surviving fingerprints")

assert created and not any(p.exists() for p in created), [p for p in created if p.exists()]
print(f'OK: all {len(created)} recorded sandboxes (lanes + gate) gone')

assert tree_hash(demo) == demo_before, 'the real demo-repo changed during the S7 verify run'
print('OK: real demo-repo byte-for-byte unchanged throughout')
"""


def _check(title: str, script: str, timeout: int, label: str) -> bool:
    print(f"=== {title} ===")
    rc, out = _run_script(script, timeout=timeout)
    ok = rc == 0
    print(out.rstrip() if ok else out[-4000:])
    print(f"  {label} -> {'PASS' if ok else 'FAIL'}")
    return ok


def check_phase18_s5() -> bool:
    """Read-only critic with a JSON verdict drives at most one revision (S5)."""
    return _check("Phase 18 S5: read-only critic, JSON verdict", _PHASE18_S5_SCRIPT, 1800, "critic + revision")


def check_phase18_s6() -> bool:
    """Fan-in conflict/abort/rollback and the --swarm CLI flag (S6)."""
    return _check("Phase 18 S6: fan-in, Gate rollback, --swarm", _PHASE18_S6_SCRIPT, 900, "fan-in + Gate")


def check_phase18_s7() -> bool:
    """Credential-free swarm end to end reaches the documented "after" numbers (S7)."""
    return _check("Phase 18 S7: credential-free swarm end to end", _PHASE18_S7_SCRIPT, 3600, "swarm end to end")
