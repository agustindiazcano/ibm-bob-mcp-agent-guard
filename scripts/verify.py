"""
scripts/verify.py — Phase verification gate.

Usage:
    python scripts/verify.py <phase-check>

Runs the checks relevant to the specified phase and prints PASS or FAIL with
measured numbers suitable for pasting into a PR description.

Phase checks implemented:
    phase0      — package installs cleanly, `repoguard --help` exits 0
    phase3      — AST mutation engine is deterministic (two runs produce identical results)
    phase7      — MCP tools accept `detail` param; compact response is the default
    phase15     — narrative.py degrades gracefully with no AI credentials
    phase16     — fix-loop write guard + fail-loud credential check
    multicloud  — ai_providers.get_provider() dispatch, defaults, and unknown-provider handling
    phase18-seq-stub — sequential fix loop driven by ScriptedProvider (no credentials), pinned after-numbers
    phase18-s1  — parallel mutation workers, single-file scope, NoMutantsError, sham-mutant control
    phase17-engine / phase18-s2 — per-mutant records + stable fingerprints, per-test JUnit outcomes
    phase14fix  — POST /api/fix: token gate, single-run lock, NDJSON events, sandbox leaves the target repo untouched
"""

from __future__ import annotations

import subprocess
import sys


def run(cmd: list[str], timeout: int = 30) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout + proc.stderr


def check_phase0() -> bool:
    print("=== Phase 0: project skeleton ===")
    rc, out = run(["repoguard", "--help"])
    ok = rc == 0 and "repoguard" in out.lower()
    status = "PASS" if ok else "FAIL"
    print(f"  repoguard --help  -> {status}")
    if not ok:
        print(out[:500])
    return ok


def check_phase3() -> bool:
    """Run mutation engine twice on demo-repo and confirm identical results."""
    print("=== Phase 3: AST mutation engine determinism ===")

    script = (
        "from repoguard_engine.core import run_mutation; "
        "r = run_mutation('demo-repo', paths_to_mutate='shop', tests_dir='tests'); "
        "print(r.score, r.killed, r.survived, r.total)"
    )

    print("  Run 1 ...", end=" ", flush=True)
    rc1, out1 = run([sys.executable, "-c", script], timeout=600)
    print(out1.strip())

    print("  Run 2 ...", end=" ", flush=True)
    rc2, out2 = run([sys.executable, "-c", script], timeout=600)
    print(out2.strip())

    if rc1 != 0 or rc2 != 0:
        print("  ERROR: mutation run failed")
        return False

    deterministic = out1.strip() == out2.strip()
    status = "PASS" if deterministic else "FAIL"
    print(f"  Determinism check -> {status}")
    if not deterministic:
        print(f"  Run 1: {out1.strip()!r}")
        print(f"  Run 2: {out2.strip()!r}")
        return False

    # Two runs agreeing isn't enough on its own -- they can agree on a
    # consistently *wrong* answer (e.g. every mutant "killed" because pytest
    # itself failed to run in every subprocess, not because tests caught
    # anything). Cross-check against the documented AGENTS.md Section 7
    # baseline: killed=16, total=79.
    try:
        _score, killed_str, _survived, total_str = out1.strip().split()
        killed, total = int(float(killed_str)), int(float(total_str))
    except ValueError:
        print(f"  ERROR: could not parse mutation output: {out1.strip()!r}")
        return False

    baseline_ok = killed == 16 and total == 79
    print(f"  Baseline check (expect killed=16, total=79) -> {'PASS' if baseline_ok else 'FAIL'}")
    if not baseline_ok:
        print(f"  Got killed={killed}, total={total} -- see AGENTS.md Section 7 for the documented baseline.")
    return baseline_ok


def check_phase7() -> bool:
    """Verify all 8 MCP tools accept detail param and return compact by default."""
    print("=== Phase 7: MCP compact responses ===")

    script = """
import ast, inspect
import repoguard_engine.mcp_server as m

tools = [
    m.tool_measure_coverage,
    m.tool_find_gaps,
    m.tool_run_mutation,
    m.tool_find_untested_endpoints,
    m.tool_smoke_test_endpoints,
    m.tool_full_pipeline,
    m.tool_capture_screenshot,
    m.tool_check_accessibility,
    m.tool_generate_summary,
]
missing = []
for fn in tools:
    sig = inspect.signature(fn)
    if 'detail' not in sig.parameters:
        missing.append(fn.__name__)
    elif sig.parameters['detail'].default is not False:
        missing.append(fn.__name__ + ' (default not False)')
if missing:
    print('MISSING detail param:', missing)
    raise SystemExit(1)
print('All 9 tools have detail:bool=False')
"""

    rc, out = run([sys.executable, "-c", script], timeout=30)
    ok = rc == 0
    status = "PASS" if ok else "FAIL"
    print(f"  {out.strip()}")
    print(f"  detail param check -> {status}")
    return ok


def check_phase15() -> bool:
    """Verify the narrative module degrades gracefully instead of
    fabricating a summary when credentials aren't configured."""
    print("=== Phase 15: AI narrative summary ===")

    script = """
import os
for var in ('WATSONX_APIKEY', 'WATSONX_PROJECT_ID', 'VERTEX_PROJECT_ID', 'REPOGUARD_AI_PROVIDER'):
    os.environ.pop(var, None)
from repoguard_engine.narrative import generate_summary
r = generate_summary({'coverage': {'percent': 1.0}, 'gaps': {'uncovered_files': []}, 'mutation': None, 'risk': []})
assert r.ok is False, 'expected ok=False with no credentials configured'
assert r.text == '', 'expected no fabricated text'
assert r.error, 'expected a real error message'
print('OK:', r.error)
"""

    rc, out = run([sys.executable, "-c", script], timeout=30)
    ok = rc == 0
    status = "PASS" if ok else "FAIL"
    print(f"  {out.strip()}")
    print(f"  no-credentials graceful-degradation check -> {status}")
    return ok


def check_phase16() -> bool:
    """Verify the AI fix-loop orchestrator's safety guard and fail-loud
    credential check -- the two properties that must hold with no live
    provider account available."""
    print("=== Phase 16: AI fix-loop orchestrator ===")

    script = """
import os, tempfile
from pathlib import Path

for var in ('WATSONX_APIKEY', 'WATSONX_PROJECT_ID', 'VERTEX_PROJECT_ID', 'REPOGUARD_AI_PROVIDER'):
    os.environ.pop(var, None)

from repoguard_engine.watson_agent.tools import write_test_file, read_source_file, SourceEditRejected
from repoguard_engine.ai_providers import get_provider, AIProviderError

with tempfile.TemporaryDirectory() as tmp:
    repo = Path(tmp)
    (repo / 'tests').mkdir()
    (repo / 'shop').mkdir()
    (repo / 'shop' / 'pricing.py').write_text('x = 1')

    # Allowed: a write under tests/
    write_test_file(str(repo), 'tests/test_new.py', 'def test_x(): assert True')
    assert (repo / 'tests' / 'test_new.py').exists(), 'expected the guarded write to succeed under tests/'

    # Rejected: a write outside tests/
    try:
        write_test_file(str(repo), 'shop/pricing.py', 'x = 2')
        raise AssertionError('expected SourceEditRejected for a write outside tests/')
    except SourceEditRejected:
        pass

    # Rejected: path traversal out of the repo
    try:
        read_source_file(str(repo), '../outside.py')
        raise AssertionError('expected SourceEditRejected for a path escaping the repo')
    except SourceEditRejected:
        pass

# Fail loud, not silent, with no credentials configured
try:
    get_provider()
    raise AssertionError('expected AIProviderError with no credentials configured')
except AIProviderError as exc:
    assert str(exc), 'expected a real error message'

print('OK: write guard enforced, path traversal rejected, fail-loud credential check confirmed')
"""

    rc, out = run([sys.executable, "-c", script], timeout=30)
    ok = rc == 0
    status = "PASS" if ok else "FAIL"
    print(f"  {out.strip()}")
    print(f"  fix-loop safety guard + fail-loud credential check -> {status}")
    return ok


def check_multicloud() -> bool:
    """Verify ai_providers.get_provider()'s dispatch: default-to-vertex
    fail-loud behavior, an unrecognized provider name failing loud, and that
    watson_agent/orchestrator.py + narrative.py import cleanly now that
    watson_agent/client.py no longer exists."""
    print("=== Multicloud: ai_providers.get_provider() dispatch ===")

    script = """
import os
os.environ.pop('WATSONX_APIKEY', None)
os.environ.pop('WATSONX_PROJECT_ID', None)
os.environ.pop('VERTEX_PROJECT_ID', None)
os.environ.pop('REPOGUARD_AI_PROVIDER', None)

from repoguard_engine.ai_providers import get_provider, AIProviderError

from repoguard_engine.ai_providers import DEFAULT_PROVIDER, resolve_provider_name

# Default (unset REPOGUARD_AI_PROVIDER) resolves to vertex and fails loud
assert DEFAULT_PROVIDER == 'vertex' and resolve_provider_name() == 'vertex', 'expected vertex as the default provider'
try:
    get_provider()
    raise AssertionError('expected AIProviderError for the default (vertex) provider with no VERTEX_PROJECT_ID')
except AIProviderError as exc:
    assert str(exc), 'expected a real error message'

# watsonx, explicitly selected, fails loud with no credentials configured
try:
    get_provider(provider='watsonx')
    raise AssertionError('expected AIProviderError for watsonx with no credentials configured')
except AIProviderError as exc:
    assert str(exc), 'expected a real error message'

# An unrecognized provider name fails loud, never silently falls back
try:
    get_provider(provider='bogus')
    raise AssertionError('expected AIProviderError for an unknown provider name')
except AIProviderError as exc:
    assert str(exc), 'expected a real error message'

# Callers of the abstraction still import cleanly (watson_agent/client.py is gone)
import repoguard_engine.narrative
import repoguard_engine.watson_agent.orchestrator

print('OK: default is vertex and fails loud, watsonx fails loud, unknown-provider fail-loud, callers import cleanly')
"""

    rc, out = run([sys.executable, "-c", script], timeout=30)
    ok = rc == 0
    status = "PASS" if ok else "FAIL"
    print(f"  {out.strip()}")
    print(f"  provider dispatch check -> {status}")
    return ok


def check_phase14fix() -> bool:
    """Verify POST /api/fix without AI credentials: token gate (503/401),
    single-run lock (409), NDJSON event order, the written tests coming back
    in `done`, and that the target repo is left byte-identical and the
    sandbox copy deleted. run_fix_loop is replaced by a stub -- this checks
    the HTTP/sandbox layer, not a live AI run."""
    print("=== Phase 14 gap 3: POST /api/fix (stubbed fix loop) ===")

    script = """
import hashlib, json, os
from pathlib import Path
from fastapi.testclient import TestClient
import repoguard_engine.watson_agent as wa
from repoguard_engine.watson_agent.orchestrator import FixResult
from repoguard_engine.web import fix_job
from repoguard_engine.web.server import app

demo = Path('demo-repo').resolve()
def tree_hash(root):
    h = hashlib.sha256()
    for p in sorted(root.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and 'repoguard-out' not in p.parts:
            h.update(str(p.relative_to(root)).encode()); h.update(p.read_bytes())
    return h.hexdigest()
before = tree_hash(demo)

seen = {}
def stub(repo_path, *, gate_threshold, publish, provider, on_event):
    assert publish is False, 'HTTP runs must never publish'
    work = Path(repo_path)
    assert work.resolve() != demo, 'fix loop must run on a copy, not the target repo'
    seen['work'] = work
    on_event('baseline_start', {})
    on_event('baseline_done', {'dashboard': {'mutation': {'score': 20.25}}, 'files': ['shop/pricing.py']})
    on_event('writer_start', {'file': 'shop/pricing.py'})
    (work / 'tests' / 'test_stub_written.py').write_text('def test_x():\\n    assert True\\n')
    on_event('critic_start', {'file': 'shop/pricing.py'})
    on_event('remeasure_start', {})
    on_event('remeasure_done', {'dashboard': {}, 'passed_gate': True})
    ev = work / 'watson-evidence'; ev.mkdir(exist_ok=True); (ev / '01-fix-loop.md').write_text('# stub evidence')
    return FixResult(repo_path=str(work), baseline={'b': 1}, after={'a': 1},
                     files_attempted=['shop/pricing.py'], critic_notes=['shop/pricing.py: ok'],
                     evidence_path=str(ev / '01-fix-loop.md'))
wa.run_fix_loop = stub

client = TestClient(app)
body = {'repo_path': str(demo)}

os.environ.pop('REPOGUARD_FIX_TOKEN', None)
assert client.post('/api/fix', json=body).status_code == 503, 'expected 503 with no REPOGUARD_FIX_TOKEN'
os.environ['REPOGUARD_FIX_TOKEN'] = 'right'
assert client.post('/api/fix', json=body).status_code == 401, 'expected 401 with no token'
assert client.post('/api/fix', json=body, headers={'Authorization': 'Bearer wrong'}).status_code == 401, 'expected 401 with a wrong token'
auth = {'Authorization': 'Bearer right'}
assert client.post('/api/fix', json={'repo_path': '/no/such/dir'}, headers=auth).status_code == 400, 'expected 400 for a bad repo_path'

fix_job._run_lock.acquire()
try:
    assert client.post('/api/fix', json=body, headers=auth).status_code == 409, 'expected 409 while a run holds the lock'
finally:
    fix_job._run_lock.release()

res = client.post('/api/fix', json=body, headers=auth)
assert res.status_code == 200, res.text
assert res.headers['content-type'].startswith('application/x-ndjson')
events = [json.loads(line) for line in res.text.splitlines() if line.strip()]
types = [e['type'] for e in events if e['type'] != 'heartbeat']
expected = ['start', 'baseline_start', 'baseline_done', 'writer_start', 'critic_start', 'remeasure_start', 'remeasure_done', 'done']
assert types == expected, f'event order {types}'
done = events[-1]['data']
assert [f['path'] for f in done['files']] == ['tests/test_stub_written.py'], done['files']
assert done['files'][0]['status'] == 'added'
assert done['evidence'] == '# stub evidence'
assert not seen['work'].exists(), 'sandbox copy was not deleted'
assert not fix_job._run_lock.locked(), 'run lock not released'
assert tree_hash(demo) == before, 'demo-repo changed during an Autofix run'

print(f'OK: 503/401/400/409 gates, {len(types)} events in order, 1 test file returned, sandbox deleted, demo-repo unchanged')
"""

    rc, out = run([sys.executable, "-c", script], timeout=60)
    ok = rc == 0
    status = "PASS" if ok else "FAIL"
    print(f"  {out.strip()}")
    print(f"  /api/fix gate + sandbox check -> {status}")
    return ok


def check_phase18_seq_stub() -> bool:
    """Run the real sequential fix loop, credential-free, on a temp copy of
    demo-repo with ScriptedProvider writing the docs/expected-after-tests/
    reference file for each file the loop picks. Pins the measured after
    numbers (3 of 4 files picked by risk -> 68/79, not the 4-file 71/79) and
    checks the timing fields H1 needs exist."""
    print("=== Phase 18 S0: sequential fix loop, scripted provider ===")

    script = """
import shutil, tempfile
from pathlib import Path
from repoguard_engine.testing import ScriptedProvider
from repoguard_engine.watson_agent import run_fix_loop

tmp = Path(tempfile.mkdtemp(prefix='repoguard_seqstub_')) / 'demo-repo'
shutil.copytree('demo-repo', tmp, ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache', 'repoguard-out', 'watson-evidence'))
try:
    provider = ScriptedProvider('docs/expected-after-tests')
    r = run_fix_loop(str(tmp), model=provider)
    before, after = r.baseline, r.after
    assert (before['mutation']['killed'], before['mutation']['total']) == (16, 79), before['mutation']
    assert r.files_attempted == ['shop/inventory.py', 'shop/api.py', 'shop/pricing.py'], r.files_attempted
    # Measured once for real (Session 23) and pinned -- 3 reference files, cart's left out by the risk cap.
    assert (after['mutation']['killed'], after['mutation']['total']) == (68, 79), after['mutation']
    assert after['mutation']['score'] == 86.08, after['mutation']
    assert round(after['coverage']['percent'], 2) == 98.64, after['coverage']
    stages = [t['stage'] for t in r.timings]
    assert stages == ['baseline'] + ['writer', 'critic'] * 3 + ['remeasure'], stages
    assert r.wall_s and r.wall_s > 0
    assert 'Wall time:' in Path(r.evidence_path).read_text(encoding='utf-8')
    assert [c['role'] for c in provider.calls].count('writer') == 9
    print(f"OK: {before['mutation']['score']}% -> {after['mutation']['score']}% ({after['mutation']['killed']}/79), "
          f"coverage {round(before['coverage']['percent'], 1)}% -> {round(after['coverage']['percent'], 2)}%, wall {r.wall_s:.1f} s")
finally:
    shutil.rmtree(tmp.parent, ignore_errors=True)
"""

    rc, out = run([sys.executable, "-c", script], timeout=900)
    ok = rc == 0
    status = "PASS" if ok else "FAIL"
    print(f"  {out.strip()}")
    print(f"  scripted sequential fix loop -> {status}")
    return ok


_TEMP_DEMO_COPY = """
import shutil, tempfile
from pathlib import Path
from repoguard_engine.core import COPY_IGNORE
def temp_demo_copy():
    tmp = Path(tempfile.mkdtemp(prefix='repoguard_verify_')) / 'demo-repo'
    shutil.copytree('demo-repo', tmp, ignore=COPY_IGNORE)
    return tmp
"""


def check_phase18_s1() -> bool:
    """Mutation engine S1: parallel workers give identical results, single-
    file scope works and sums to the whole-repo run, an empty scope fails
    loud, and the sham-mutant control catches a suite that only fails in a
    copy (the false-100% class). All on a temp copy of demo-repo."""
    print("=== Phase 18 S1: parallel mutation, file scope, zero-mutant and sham guards ===")

    script = _TEMP_DEMO_COPY + """
import time
from repoguard_engine.core import run_mutation, NoMutantsError, MutationEnvironmentError
tmp = temp_demo_copy()
try:
    t = time.perf_counter(); r1 = run_mutation(tmp, 'shop'); w1 = time.perf_counter() - t
    t = time.perf_counter(); r4 = run_mutation(tmp, 'shop', workers=4); w4 = time.perf_counter() - t
    for r in (r1, r4):
        assert (r.score, r.killed, r.survived, r.total) == (20.25, 16, 63, 79), (r.score, r.killed, r.total)
    assert r1.surviving_mutant_ids == r4.surviving_mutant_ids
    print(f'workers=1 {w1:.1f} s, workers=4 {w4:.1f} s, both 20.25% 16/79, identical survivors')

    total = killed = 0
    for f in ('api', 'cart', 'inventory', 'pricing'):
        r = run_mutation(tmp, f'shop/{f}.py', workers=4)
        assert r.total > 0, f
        total += r.total; killed += r.killed
    assert (total, killed) == (79, 16), (total, killed)
    print('file-scoped runs sum to 79 mutants, 16 killed')

    try:
        run_mutation(tmp, 'shop/__init__.py')
        raise AssertionError('expected NoMutantsError for a file with no mutation sites')
    except NoMutantsError:
        pass

    probe = tmp / 'tests' / 'test_copy_probe.py'
    probe.write_text("def test_not_in_a_copy():\\n    assert 'repoguard_mutant_' not in __file__\\n")
    try:
        run_mutation(tmp, 'shop/pricing.py')
        raise AssertionError('expected MutationEnvironmentError: suite fails only in a copy')
    except MutationEnvironmentError:
        pass
    probe.unlink()

    assert not list(tmp.rglob('__pycache__')), 'bytecode written into the target repo'
    print('OK: empty scope -> NoMutantsError, copy-only failure -> MutationEnvironmentError, no __pycache__')
finally:
    shutil.rmtree(tmp.parent, ignore_errors=True)
"""

    rc, out = run([sys.executable, "-c", script], timeout=900)
    ok = rc == 0
    print("  " + out.strip().replace("\n", "\n  "))
    print(f"  S1 engine checks -> {'PASS' if ok else 'FAIL'}")
    return ok


def check_phase17_engine() -> bool:
    """Per-mutant records (Phase 17 A2.1 / Phase 18 S2) and per-test outcomes
    (A2.2): 79 records, unique and stable fingerprints, identical across
    runs, 5 passing tests on demo-repo, correct JUnit outcome mapping, and
    the after-reference suite's 71 passing tests."""
    print("=== Phase 17 A2 / Phase 18 S2: per-mutant and per-test records ===")

    script = _TEMP_DEMO_COPY + """
import json
from repoguard_engine.core import run_mutation, measure_coverage
from repoguard_engine.mutation import _generate_mutants
tmp = temp_demo_copy()
try:
    a = run_mutation(tmp, 'shop', workers=4)
    b = run_mutation(tmp, 'shop', workers=4)
    rec = lambda r: [(m.index, m.fingerprint, m.outcome) for m in r.mutants]
    assert rec(a) == rec(b), 'two runs gave different per-mutant records'
    assert len(a.mutants) == 79 and sum(m.outcome != 'survived' for m in a.mutants) == 16
    assert [m.index for m in a.mutants if m.outcome == 'survived'] == a.surviving_mutant_ids
    assert len({m.fingerprint for m in a.mutants}) == 79, 'fingerprints not unique'
    assert all(m.file and m.function and m.lineno > 0 and m.operator and m.description for m in a.mutants)
    counts = a.outcome_counts()
    out = json.loads((tmp / 'repoguard-out' / 'mutants.json').read_text())
    assert len(out['mutants']) == 79 and out['counts'] == counts
    assert sorted(json.loads((tmp / 'repoguard-out' / 'mutation.json').read_text())) == ['killed', 'score', 'survived', 'surviving_mutant_ids', 'total']
    print(f"79 records, 16 killed, unique fingerprints, identical across 2 runs, timeouts={counts['timeout']} errors={counts['error']}")

    # Stability: adding a new function to a copy of cart.py keeps every
    # existing fingerprint; only the new function's mutants are new.
    cart = tmp / 'shop' / 'cart.py'
    before = {m.fingerprint for m in _generate_mutants(cart, 'shop/cart.py', 0)}
    original_cart = cart.read_text()
    cart.write_text(original_cart + '\\n\\ndef _added_later(x):\\n    return x + 1 if x > 0 else 0\\n')
    after = _generate_mutants(cart, 'shop/cart.py', 0)
    new = [m for m in after if m.fingerprint not in before]
    assert before <= {m.fingerprint for m in after}, 'an existing fingerprint changed'
    assert new and all(m.function == '_added_later' for m in new), [m.function for m in new]
    cart.write_text(original_cart)
    print(f'fingerprint stability: {len(before)} kept, {len(new)} new (all in the added function)')

    cov = measure_coverage(tmp)
    assert round(cov.percent, 1) == 65.1 and len(cov.tests) == 5 and {t.outcome for t in cov.tests} == {'passed'}
    assert sorted(json.loads((tmp / 'repoguard-out' / 'coverage.json').read_text())) == ['covered_lines', 'missing_lines', 'percent', 'total_lines']
    for f in Path('docs/expected-after-tests').glob('test_*.py'):
        shutil.copy(f, tmp / 'tests' / f.name)
    cov = measure_coverage(tmp)
    passed = sum(t.outcome == 'passed' for t in cov.tests)
    assert passed == 71, passed
    print(f'per-test outcomes: baseline 5 passed (65.1%), after-reference {passed} passed ({cov.percent:.1f}%)')

    mix = tmp.parent / 'mix'
    (mix / 'tests').mkdir(parents=True)
    (mix / 'tests' / '__init__.py').write_text('')
    (mix / 'tests' / 'test_mix.py').write_text(
        'import pytest\\n'
        'def test_pass(): assert True\\n'
        'def test_fail(): assert 1 == 2\\n'
        '@pytest.mark.skip(reason="s")\\ndef test_skip(): pass\\n'
        '@pytest.mark.xfail(reason="x")\\ndef test_xfail(): assert False\\n'
    )
    got = {t.test_id.split('::')[1]: t.outcome for t in measure_coverage(mix).tests}
    assert got == {'test_pass': 'passed', 'test_fail': 'failed', 'test_skip': 'skipped', 'test_xfail': 'skipped'}, got
    print('OK: junit mapping pass/fail/skip/xfail correct')
finally:
    shutil.rmtree(tmp.parent, ignore_errors=True)
"""

    rc, out = run([sys.executable, "-c", script], timeout=900)
    ok = rc == 0
    print("  " + out.strip().replace("\n", "\n  "))
    print(f"  per-mutant / per-test records -> {'PASS' if ok else 'FAIL'}")
    return ok


CHECKS: dict[str, callable] = {
    "phase0": check_phase0,
    "phase3": check_phase3,
    "phase7": check_phase7,
    "phase15": check_phase15,
    "phase16": check_phase16,
    "multicloud": check_multicloud,
    "phase14fix": check_phase14fix,
    "phase18-seq-stub": check_phase18_seq_stub,
    "phase18-s1": check_phase18_s1,
    "phase17-engine": check_phase17_engine,
    "phase18-s2": check_phase17_engine,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in CHECKS:
        print(f"Usage: python scripts/verify.py <{'|'.join(CHECKS)}>")
        sys.exit(1)
    ok = CHECKS[sys.argv[1]]()
    print("\nResult:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
