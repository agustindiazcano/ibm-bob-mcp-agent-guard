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
    rc1, out1 = run(["python", "-c", script], timeout=270)
    print(out1.strip())

    print("  Run 2 ...", end=" ", flush=True)
    rc2, out2 = run(["python", "-c", script], timeout=270)
    print(out2.strip())

    if rc1 != 0 or rc2 != 0:
        print("  ERROR: mutation run failed")
        return False

    ok = out1.strip() == out2.strip()
    status = "PASS" if ok else "FAIL"
    print(f"  Determinism check -> {status}")
    if not ok:
        print(f"  Run 1: {out1.strip()!r}")
        print(f"  Run 2: {out2.strip()!r}")
    return ok


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
print('All 8 tools have detail:bool=False')
"""

    rc, out = run(["python", "-c", script], timeout=30)
    ok = rc == 0
    status = "PASS" if ok else "FAIL"
    print(f"  {out.strip()}")
    print(f"  detail param check -> {status}")
    return ok


CHECKS: dict[str, callable] = {
    "phase0": check_phase0,
    "phase3": check_phase3,
    "phase7": check_phase7,
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
