import ast
import json
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from repoguard_engine.core import pytest_env, COPY_IGNORE
from repoguard_engine.watson_agent.policy import check_test_source
from repoguard_engine.watson_agent.tools import _source_roots

def snapshot_tests(repo: Path, tests_dir: str = "tests") -> dict[str, bytes]:
    res = {}
    p = repo / tests_dir
    if p.exists():
        for f in p.rglob("*.py"):
            res[f.relative_to(repo).as_posix()] = f.read_bytes()
    return res

def collect_test_ids(repo: Path, tests_dir: str = "tests") -> set[str]:
    import sys
    cmd = [sys.executable, "-m", "pytest", tests_dir, "--collect-only"]
    proc = subprocess.run(cmd, cwd=repo, env=pytest_env(), capture_output=True, text=True)
    ids = set()
    for line in proc.stdout.splitlines():
        if "::" in line:
            ids.add(line.strip())
    return ids

def changed_test_files(before: dict[str, bytes], repo: Path) -> list[str]:
    res = []
    tests = repo / "tests"
    if not tests.exists():
        return res
    for f in tests.rglob("*.py"):
        rel = f.relative_to(repo).as_posix()
        cur = f.read_bytes()
        if rel not in before or before[rel] != cur:
            res.append(rel)
    return res

def canary_transform(source: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source
    return "# repoguard-canary\n" + ast.unparse(tree)

@dataclass
class Acceptance:
    file: str
    accepted: bool
    reasons: list[str] = field(default_factory=list)
    runs: list[int] = field(default_factory=list)
    xfail: int = 0

def _run_junit(repo: Path, test_file: str, out_xml: Path) -> tuple[int, dict[str, str], str, str]:
    import sys
    cmd = [sys.executable, "-m", "pytest", test_file, f"--junitxml={out_xml}"]
    proc = subprocess.run(cmd, cwd=repo, env=pytest_env(), capture_output=True, text=True)
    if not out_xml.exists():
        return proc.returncode, {}, proc.stdout, proc.stderr
    
    try:
        tree = ET.parse(out_xml)
        outcomes = {}
        for testcase in tree.findall(".//testcase"):
            name = f"{testcase.get('classname')}::{testcase.get('name')}"
            if testcase.find("failure") is not None:
                outcomes[name] = "failure"
            elif testcase.find("error") is not None:
                outcomes[name] = "error"
            elif testcase.find("skipped") is not None:
                outcomes[name] = "skipped"
            else:
                outcomes[name] = "passed"
        return proc.returncode, outcomes, proc.stdout, proc.stderr
    except Exception:
        return proc.returncode, {}, proc.stdout, proc.stderr

def accept_file(repo: Path, test_file: str, *, runs: int = 3) -> Acceptance:
    target_path = repo / test_file
    if target_path.is_file():
        try:
            src = target_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            src = target_path.read_text(encoding="latin1")
        violations = check_test_source(src, test_file, source_roots=_source_roots(repo))
        if violations:
            return Acceptance(test_file, False, [f"Policy: {v.rule}" for v in violations])
    
    exit_codes = []
    base_outcomes = None
    with tempfile.TemporaryDirectory() as td:
        for i in range(runs):
            xml = Path(td) / f"out_{i}.xml"
            rc, outcomes, stdout, stderr = _run_junit(repo, test_file, xml)
            exit_codes.append(rc)
            if rc != 0:
                err_msg = f"Repetition: non-zero exit code ({rc})\\nSTDOUT:\\n{stdout[-1000:]}\\nSTDERR:\\n{stderr[-1000:]}"
                return Acceptance(test_file, False, [err_msg], exit_codes)
            if base_outcomes is None:
                base_outcomes = outcomes
            elif base_outcomes != outcomes:
                return Acceptance(test_file, False, ["Repetition: flaky test outcomes"], exit_codes)

    with tempfile.TemporaryDirectory() as tmp:
        sandbox = Path(tmp) / "sandbox"
        shutil.copytree(repo, sandbox, ignore=COPY_IGNORE)
        
        for root in _source_roots(sandbox):
            for py in (sandbox / root).rglob("*.py"):
                text = py.read_text(encoding="utf-8")
                canary_text = canary_transform(text)
                py.write_text(canary_text, encoding="utf-8")
        
        xml = Path(tmp) / "canary.xml"
        rc, _, _, _ = _run_junit(sandbox, test_file, xml)
        if rc != 0:
            return Acceptance(test_file, False, ["Canary: fails on unmodified semantics"], exit_codes)

    return Acceptance(test_file, True, [], exit_codes)

def quarantine(repo: Path, test_file: str, acceptance: Acceptance, run_id: str, original: bytes | None) -> str:
    dest_dir = repo / "watson-evidence" / "quarantine" / run_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    tgt = repo / test_file
    dest_txt = dest_dir / f"{Path(test_file).name}.txt"
    dest_json = dest_dir / f"{Path(test_file).name}.reason.json"
    
    if tgt.exists():
        dest_txt.write_bytes(tgt.read_bytes())
    
    dest_json.write_text(json.dumps({"reasons": acceptance.reasons, "runs": acceptance.runs}))
    
    if original is not None:
        tgt.write_bytes(original)
    else:
        tgt.unlink(missing_ok=True)
        
    return str(dest_txt)
