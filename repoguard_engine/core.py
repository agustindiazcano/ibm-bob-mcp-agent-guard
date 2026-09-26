"""Core measurement functions: coverage, gaps, risk, dashboard.

The AST mutation engine lives in mutation.py; its public names are
re-exported here so `from repoguard_engine.core import run_mutation` keeps
working.
"""

from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from ._common import COPY_IGNORE, require_repo_dir as _require_repo_dir, write_out as _write_out
from .mutation import (
    MUTATION_ENGINE_REVISION,
    MUTATION_OPERATORS_HASH,
    MutantRecord,
    MutationEnvironmentError,
    MutationResult,
    NoMutantsError,
    run_mutation,
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CaseOutcome:
    """One test's result from the coverage run. test_id is JUnit's
    `classname::name` (e.g. tests.test_cart::test_add[2]) -- composed, not
    pytest's exact nodeid. duration_s is recorded but never compared: it's
    wall time under coverage instrumentation, not deterministic."""
    test_id: str
    outcome: str  # passed | failed | error | skipped (xfail counts as skipped)
    duration_s: float
    message: str = ""


@dataclass
class CoverageResult:
    percent: float
    covered_lines: int
    total_lines: int
    missing_lines: dict[str, list[int]] = field(default_factory=dict)
    # Per-test outcomes. Kept out of repoguard-out/coverage.json (unchanged
    # format) and written to repoguard-out/tests.json.
    tests: list[CaseOutcome] = field(default_factory=list)


@dataclass
class GapReport:
    uncovered_functions: list[str] = field(default_factory=list)
    uncovered_files: list[str] = field(default_factory=list)
    missing_lines_by_file: dict[str, list[int]] = field(default_factory=dict)


@dataclass
class RiskScore:
    file: str
    score: float  # 0.0 – 1.0
    reasons: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Coverage
# ---------------------------------------------------------------------------

def measure_coverage(repo_path: str | Path) -> CoverageResult:
    """Run pytest with coverage on *repo_path*, write repoguard-out/coverage.json, return CoverageResult."""
    repo = _require_repo_dir(repo_path)
    # Per-run data/report paths: concurrent measurements of the same repo
    # (e.g. /api/analyze + /api/stream) would otherwise erase each other's
    # .coverage and read a half-written coverage.json.
    with tempfile.TemporaryDirectory(prefix="repoguard-cov-") as tmp:
        coverage_json = Path(tmp) / "coverage.json"
        junit_xml = Path(tmp) / "junit.xml"
        proc = subprocess.run(
            [
                sys.executable, "-m", "pytest", "--cov", f"--cov-report=json:{coverage_json}",
                f"--junitxml={junit_xml}", "-q", "--tb=no",
            ],
            cwd=repo,
            env={**os.environ, "COVERAGE_FILE": str(Path(tmp) / ".coverage"), "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
            timeout=120,
        )
        if not coverage_json.exists():
            # A missing coverage.json means pytest/pytest-cov failed to run, not
            # that the repo has 0% coverage — report the failure instead of a
            # fabricated zero (AGENTS.md: never claim a result you did not measure).
            raise RuntimeError(
                f"pytest did not produce coverage.json (exit code {proc.returncode}).\n"
                f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
            )
        data = json.loads(coverage_json.read_text(encoding="utf-8"))
        tests = _parse_junit(junit_xml)

    totals = data.get("totals", {})
    missing: dict[str, list[int]] = {}
    for fname, fdata in data.get("files", {}).items():
        if fdata.get("missing_lines"):
            missing[fname] = fdata["missing_lines"]

    result = CoverageResult(
        percent=totals.get("percent_covered", 0.0),
        covered_lines=totals.get("covered_lines", 0),
        total_lines=totals.get("num_statements", 0),
        missing_lines=missing,
        tests=tests,
    )
    _write_out(repo, "coverage", {k: v for k, v in dataclasses.asdict(result).items() if k != "tests"})
    _write_out(repo, "tests", [dataclasses.asdict(t) for t in tests])
    return result


def _parse_junit(path: Path) -> list[CaseOutcome]:
    """Per-test outcomes from pytest's --junitxml report (stdlib only).
    A missing report (pytest crashed before writing it) yields []."""
    if not path.exists():
        return []
    outcomes: list[CaseOutcome] = []
    for case in ET.parse(path).getroot().iter("testcase"):
        classname = case.get("classname", "")
        name = case.get("name", "")
        test_id = f"{classname}::{name}" if classname else name
        outcome, message = "passed", ""
        for tag in ("failure", "error", "skipped"):
            child = case.find(tag)
            if child is not None:
                outcome = {"failure": "failed", "error": "error", "skipped": "skipped"}[tag]
                message = (child.get("message") or "")[:500]
                break
        outcomes.append(CaseOutcome(test_id, outcome, float(case.get("time") or 0.0), message))
    return outcomes


def find_coverage_gaps(coverage: CoverageResult, repo_path: str | Path | None = None) -> GapReport:
    """Derive a structured gap report from a CoverageResult, write repoguard-out/gaps.json if repo_path given."""
    gap = GapReport()
    gap.missing_lines_by_file = dict(coverage.missing_lines)
    gap.uncovered_files = [f for f, lines in coverage.missing_lines.items() if lines]
    if repo_path is not None:
        _write_out(Path(repo_path), "gaps", dataclasses.asdict(gap))
    return gap


# ---------------------------------------------------------------------------
# Risk
# ---------------------------------------------------------------------------

def compute_risk(repo_path: str | Path, coverage: CoverageResult) -> list[RiskScore]:
    """Assign a risk score to each file based on coverage gaps and file size. Writes repoguard-out/risk.json."""
    repo = Path(repo_path)
    scores: list[RiskScore] = []
    for fname, missing in coverage.missing_lines.items():
        path = repo / fname
        try:
            total_lines = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        except OSError:
            total_lines = 1

        coverage_gap = len(missing) / max(total_lines, 1)
        risk = RiskScore(
            file=fname,
            score=round(min(coverage_gap, 1.0), 3),
            reasons=[f"{len(missing)} uncovered lines out of ~{total_lines}"],
        )
        scores.append(risk)

    scores.sort(key=lambda r: r.score, reverse=True)
    _write_out(repo, "risk", [dataclasses.asdict(r) for r in scores])
    return scores


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def build_dashboard_data(
    coverage: CoverageResult,
    gap: GapReport,
    mutation: MutationResult | None = None,
    risk: list[RiskScore] | None = None,
) -> dict:
    """Assemble a JSON-serialisable dict for the web dashboard."""
    return {
        "coverage": {
            "percent": coverage.percent,
            "covered_lines": coverage.covered_lines,
            "total_lines": coverage.total_lines,
        },
        "gaps": {
            "uncovered_files": gap.uncovered_files,
            "missing_lines_by_file": gap.missing_lines_by_file,
        },
        "mutation": (
            {
                "score": mutation.score,
                "killed": mutation.killed,
                "survived": mutation.survived,
                "total": mutation.total,
            }
            if mutation
            else None
        ),
        "risk": (
            [{"file": r.file, "score": r.score, "reasons": r.reasons} for r in risk]
            if risk
            else []
        ),
    }
