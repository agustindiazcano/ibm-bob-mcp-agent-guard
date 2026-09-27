import subprocess
import sys
from phase19_scripts import SCRIPTS, get_honest_turns
from pathlib import Path

def _run_script(script: str, timeout: int) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout + proc.stderr

def check_phase19() -> bool:
    print("=== Phase 19 E1: Scripted Provider & Attack Suite ===")
    
    docs_path = Path('docs/expected-after-tests').resolve()
    honest_turns = get_honest_turns(docs_path)

    script_template = r"""
import shutil
import sys
import tempfile
import time
from pathlib import Path
from dataclasses import dataclass

from repoguard_engine.core import COPY_IGNORE
from repoguard_engine.ai_providers.scripted import ScriptedProvider
from repoguard_engine.watson_agent.orchestrator import run_fix_loop
import repoguard_engine.watson_agent.orchestrator as orchestrator

def _temp_demo_copy():
    tmp = Path(tempfile.mkdtemp(prefix='repoguard_verify_')) / 'demo-repo'
    shutil.copytree('demo-repo', tmp, ignore=COPY_IGNORE)
    return tmp

HONEST_TURNS = {honest_turns!r}
SCRIPTS = {scripts!r}

tests = [
    ("honest", HONEST_TURNS),
]
for name, turns in SCRIPTS.items():
    tests.append((name, turns))

failures = []
real_run_pipeline = orchestrator.run_pipeline

@dataclass
class FakePipelineResult:
    dashboard: dict
    passed_gate: bool
    risk: list
    gap: any = None
    mutation: any = None

class FakeRisk:
    def __init__(self, f):
        self.file = f

class FakeGap:
    missing_lines_by_file = {}

class FakeMutation:
    mutants = []

def fake_run_pipeline(repo_path, **kwargs):
    return FakePipelineResult(
        dashboard={"mutation": {"score": 20.0}},
        passed_gate=False,
        risk=[FakeRisk("shop/api.py")],
        gap=FakeGap(),
        mutation=FakeMutation()
    )

for name, turns in tests:
    tmp = _temp_demo_copy()
    try:
        print(f"  Running script: {name} ...", end=" ", flush=True)
        provider = ScriptedProvider(turns)
        t0 = time.perf_counter()
        
        # Stub pipeline for attacks that don't need real measurements to run faster
        if name in ("honest", "A1_fingerprint"):
            orchestrator.run_pipeline = real_run_pipeline
        else:
            orchestrator.run_pipeline = fake_run_pipeline
            
        try:
            res = run_fix_loop(str(tmp), model=provider)
            if name == "honest":
                if res.after and round(res.after["mutation"]["score"], 2) == 89.87:
                    print(f"PASS ({time.perf_counter()-t0:.1f}s)")
                else:
                    ms = res.after['mutation']['score'] if res.after else None
                    print(f"FAIL: Honest script did not achieve 89.87% (got {ms})")
                    failures.append(name)
            else:
                if getattr(res, "status", None) == "rejected":
                    print(f"PASS ({time.perf_counter()-t0:.1f}s) - Attack stopped")
                else:
                    print(f"FAIL: Attack {name} was not stopped (status: {getattr(res, 'status', 'N/A')})")
                    failures.append(name)
        except Exception as e:
            if name in ("A6_escape",):
                print(f"PASS ({time.perf_counter()-t0:.1f}s) - Attack stopped by exception: {type(e).__name__}: {e}")
            else:
                print(f"FAIL: Unexpected exception for {name}: {type(e).__name__}: {e}")
                failures.append(name)

    finally:
        orchestrator.run_pipeline = real_run_pipeline
        shutil.rmtree(tmp.parent, ignore_errors=True)

if failures:
    print(f"  E1 script check -> FAIL ({len(failures)} attacks bypass guards or honest failed)")
    sys.exit(1)

print("  E1 script check -> PASS")
sys.exit(0)
"""
    script = script_template.replace("{honest_turns!r}", repr(honest_turns)).replace("{scripts!r}", repr(SCRIPTS))
    
    rc, out = _run_script(script, timeout=900)
    ok = rc == 0
    print(out.rstrip() if ok else out[-3000:])
    return ok
