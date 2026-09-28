"""Fan-in (Phase 18 S6, docs/MULTI_AGENT_SWARM.md Section 4.5): merge every
ACCEPTED lane's test file into the real tests/, safely.

Lanes own disjoint files, so there's no text conflict -- but there can be a
runtime one: demo-repo's shop/api.py keeps module-level singletons, so two
files that each pass alone can fail together. So:

1. Abort if the real tests/ changed since the plan was built (someone edited
   it under a long-running swarm) -- FanInAborted, nothing written.
2. Read each lane's content from its blackboard snapshot, checked against
   the sha256 recorded in result.json -- never from a (deleted) sandbox.
3. In a fresh gate sandbox, add files one at a time in sorted owned-path
   order, running the whole suite after each; a file that turns it red is
   dropped as REJECTED_AT_FANIN, naming what it was merged with.
4. Stability: the merged suite must pass STABILITY_RUNS times forward, once
   in reversed file order, and each lane file alone. If not, drop lanes in
   reverse-sorted order until it does -- flaky tests are exactly what the
   sham-mutant control can't catch.
5. Only then copy the survivors into the real tests/, remembering any file
   overwritten so rollback() can restore it byte for byte.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ..core import pytest_env
from ..watson_agent.tools import run_tests
from . import blackboard
from .lane import LaneOutcome, owned_test_path
from .plan import Plan, _tests_manifest
from .sandbox import lane_sandbox

STABILITY_RUNS = 3
_PYTEST_TIMEOUT = 300


class FanInAborted(RuntimeError):
    """The real tests/ changed between planning and fan-in; nothing was merged."""


@dataclass
class FanInResult:
    merged: list[str] = field(default_factory=list)  # modules whose file reached the real tests/
    rejected: dict[str, str] = field(default_factory=dict)  # module -> why it was dropped
    written: list[str] = field(default_factory=list)  # repo-relative posix paths written
    overwritten: dict[str, bytes] = field(default_factory=dict)  # path -> its bytes before fan-in
    stability: dict = field(default_factory=dict)


def fan_in(repo: str | Path, plan: Plan, outcomes: list[LaneOutcome], rd: Path, *, tests_dir: str = "tests") -> FanInResult:
    repo = Path(repo).resolve()
    if _tests_manifest(repo, tests_dir) != plan.tests_manifest:
        raise FanInAborted(f"{tests_dir}/ changed since the swarm plan was built; refusing to merge into it")

    result = FanInResult()
    contents: dict[str, str] = {}
    for outcome in sorted((o for o in outcomes if o.status == "ACCEPTED"), key=lambda o: owned_test_path(o.module)):
        content = blackboard.read_final_test(rd, outcome.module)
        if content is None or hashlib.sha256(content.encode("utf-8")).hexdigest() != outcome.test_sha256:
            result.rejected[outcome.module] = "final snapshot missing or its sha256 doesn't match result.json"
            continue
        contents[outcome.module] = content

    with lane_sandbox(repo, "gate") as gate:
        for module, content in contents.items():
            target = gate / owned_test_path(module)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            suite = run_tests(repo_path=str(gate))
            if suite["passed"]:
                result.merged.append(module)
                continue
            target.unlink()
            with_what = ", ".join(owned_test_path(m) for m in result.merged) or "the original tests"
            result.rejected[module] = f"suite red when merged with {with_what}: {suite['output'][-500:]}"

        stable, detail = _stability(gate, result.merged, tests_dir)
        while result.merged and not stable:
            dropped = result.merged.pop()
            (gate / owned_test_path(dropped)).unlink()
            result.rejected[dropped] = f"unstable when merged: {detail}"
            stable, detail = _stability(gate, result.merged, tests_dir)
        result.stability = {"stable": stable, "detail": detail, "forward_runs": STABILITY_RUNS}

    for module in result.merged:
        rel = owned_test_path(module)
        target = repo / rel
        if target.exists():
            result.overwritten[rel] = target.read_bytes()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(contents[module], encoding="utf-8")
        result.written.append(rel)
    return result


def rollback(repo: str | Path, result: FanInResult) -> None:
    """Undo fan-in's writes to the real tests/: restore overwritten files,
    delete the ones it added."""
    repo = Path(repo).resolve()
    for rel in result.written:
        target = repo / rel
        if rel in result.overwritten:
            target.write_bytes(result.overwritten[rel])
        else:
            target.unlink(missing_ok=True)


def _stability(gate: Path, merged: list[str], tests_dir: str) -> tuple[bool, str]:
    for i in range(STABILITY_RUNS):
        suite = run_tests(repo_path=str(gate))
        if not suite["passed"]:
            return False, f"forward run {i + 1}/{STABILITY_RUNS} failed"
    files = sorted(p.relative_to(gate).as_posix() for p in (gate / tests_dir).rglob("test_*.py"))
    if not _pytest(gate, list(reversed(files))):
        return False, "reversed file order failed"
    for module in merged:
        owned = owned_test_path(module)
        if not run_tests(repo_path=str(gate), file_path=owned)["passed"]:
            return False, f"{owned} fails when run alone"
    return True, "ok"


def _pytest(root: Path, files: list[str]) -> bool:
    if not files:
        return True
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *files, "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=root,
        env=pytest_env(),
        capture_output=True,
        text=True,
        timeout=_PYTEST_TIMEOUT,
        check=False,
    )
    return proc.returncode == 0
