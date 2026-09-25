"""Core measurement functions: coverage, gaps, mutation, risk, dashboard."""

from __future__ import annotations

import subprocess
import json
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class CoverageResult:
    percent: float
    covered_lines: int
    total_lines: int
    missing_lines: dict[str, list[int]] = field(default_factory=dict)


@dataclass
class GapReport:
    uncovered_functions: list[str] = field(default_factory=list)
    uncovered_files: list[str] = field(default_factory=list)
    missing_lines_by_file: dict[str, list[int]] = field(default_factory=dict)


@dataclass
class MutationResult:
    score: float
    killed: int
    survived: int
    total: int
    surviving_mutant_ids: list[int] = field(default_factory=list)


@dataclass
class RiskScore:
    file: str
    score: float  # 0.0 – 1.0
    reasons: list[str] = field(default_factory=list)


def measure_coverage(repo_path: str | Path) -> CoverageResult:
    """Run pytest with coverage on *repo_path* and return a CoverageResult."""
    repo = Path(repo_path)
    result = subprocess.run(
        ["pytest", "--cov", "--cov-report=json", "-q", "--tb=no"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    coverage_json = repo / "coverage.json"
    if not coverage_json.exists():
        return CoverageResult(percent=0.0, covered_lines=0, total_lines=0)

    data = json.loads(coverage_json.read_text())
    totals = data.get("totals", {})
    missing: dict[str, list[int]] = {}
    for fname, fdata in data.get("files", {}).items():
        if fdata.get("missing_lines"):
            missing[fname] = fdata["missing_lines"]

    return CoverageResult(
        percent=totals.get("percent_covered", 0.0),
        covered_lines=totals.get("covered_lines", 0),
        total_lines=totals.get("num_statements", 0),
        missing_lines=missing,
    )


def find_coverage_gaps(coverage: CoverageResult) -> GapReport:
    """Derive a structured gap report from a CoverageResult."""
    gap = GapReport()
    gap.missing_lines_by_file = dict(coverage.missing_lines)
    gap.uncovered_files = [f for f, lines in coverage.missing_lines.items() if lines]
    return gap


def run_mutation(
    repo_path: str | Path,
    paths_to_mutate: str = ".",
    tests_dir: str = "tests",
) -> MutationResult:
    """Run mutmut on *repo_path* and return a MutationResult."""
    repo = Path(repo_path)
    subprocess.run(
        [
            "mutmut",
            "run",
            f"--paths-to-mutate={paths_to_mutate}",
            f"--tests-dir={tests_dir}",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    result_proc = subprocess.run(
        ["mutmut", "results"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    # Parse simple summary line e.g. "Killed: 42, Survived: 8, Total: 50"
    killed = survived = total = 0
    for line in result_proc.stdout.splitlines():
        lower = line.lower()
        if "killed" in lower:
            try:
                killed = int(line.split(":")[1].strip().rstrip(","))
            except (IndexError, ValueError):
                pass
        elif "survived" in lower:
            try:
                survived = int(line.split(":")[1].strip().rstrip(","))
            except (IndexError, ValueError):
                pass
        elif "total" in lower:
            try:
                total = int(line.split(":")[1].strip())
            except (IndexError, ValueError):
                pass

    score = (killed / total * 100) if total else 0.0
    return MutationResult(score=score, killed=killed, survived=survived, total=total)


def compute_risk(repo_path: str | Path, coverage: CoverageResult) -> list[RiskScore]:
    """Assign a risk score to each file based on coverage gaps and file size."""
    scores: list[RiskScore] = []
    for fname, missing in coverage.missing_lines.items():
        path = Path(repo_path) / fname
        try:
            total_lines = sum(1 for _ in path.read_text().splitlines() if _.strip())
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
    return scores


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
