"""
scripts/verify.py — Phase verification gate.

Usage:
    python scripts/verify.py <phase-check>

Runs the checks relevant to the specified phase and prints PASS or FAIL with
measured numbers suitable for pasting into a PR description.

Phase checks implemented:
    phase0   — package installs cleanly, `repoguard --help` exits 0
    phase3   — AST mutation engine is deterministic (two runs produce identical results)
    phase7   — MCP tools accept `detail` param; compact response is the default
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
    """Verify the watsonx narrative module degrades gracefully instead of
    fabricating a summary when credentials aren't configured."""
    print("=== Phase 15: watsonx narrative summary ===")

    script = """
from repoguard_engine.narrative import generate_summary
import os
os.environ.pop('WATSONX_APIKEY', None)
os.environ.pop('WATSONX_PROJECT_ID', None)
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
    """Verify the watsonx.ai fix-loop orchestrator's safety guard and
    fail-loud credential check -- the two properties that must hold with no
    live IBM Cloud account available."""
    print("=== Phase 16: watsonx.ai fix-loop orchestrator ===")

    script = """
import os, tempfile
from pathlib import Path

os.environ.pop('WATSONX_APIKEY', None)
os.environ.pop('WATSONX_PROJECT_ID', None)

from repoguard_engine.watson_agent.tools import write_test_file, read_source_file, SourceEditRejected
from repoguard_engine.watson_agent.client import get_chat_model, WatsonxCredentialsError

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
    get_chat_model()
    raise AssertionError('expected WatsonxCredentialsError with no credentials configured')
except WatsonxCredentialsError as exc:
    assert str(exc), 'expected a real error message'

print('OK: write guard enforced, path traversal rejected, fail-loud credential check confirmed')
"""

    rc, out = run([sys.executable, "-c", script], timeout=30)
    ok = rc == 0
    status = "PASS" if ok else "FAIL"
    print(f"  {out.strip()}")
    print(f"  fix-loop safety guard + fail-loud credential check -> {status}")
    return ok


CHECKS: dict[str, callable] = {
    "phase0": check_phase0,
    "phase3": check_phase3,
    "phase7": check_phase7,
    "phase15": check_phase15,
    "phase16": check_phase16,
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
