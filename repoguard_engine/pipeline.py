"""Pipeline execution: measure mode and bob-fix mode."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .core import (
    measure_coverage,
    find_coverage_gaps,
    run_mutation,
    compute_risk,
    build_dashboard_data,
    CoverageResult,
    GapReport,
    MutationResult,
    RiskScore,
)
from .api_check import find_untested_endpoints


@dataclass
class PipelineResult:
    repo_path: str
    coverage: CoverageResult | None = None
    gap: GapReport | None = None
    mutation: MutationResult | None = None
    risk: list[RiskScore] = field(default_factory=list)
    endpoints: list = field(default_factory=list)
    dashboard: dict = field(default_factory=dict)
    passed_gate: bool = False
    gate_threshold: float = 80.0


def run_pipeline(
    repo_path: str | Path,
    *,
    include_mutation: bool = False,
    include_endpoints: bool = True,
    gate_threshold: float = 80.0,
    mutation_workers: int = 1,
) -> PipelineResult:
    """
    Full measurement pipeline.

    Steps:
    1. Run pytest + coverage
    2. Derive gap report
    3. Optionally run mutation testing (mutation_workers in parallel)
    4. Optionally detect untested FastAPI endpoints
    5. Compute risk scores
    6. Assemble dashboard data
    7. Evaluate gate threshold
    """
    repo = Path(repo_path)
    result = PipelineResult(repo_path=str(repo), gate_threshold=gate_threshold)

    # 1. Coverage
    result.coverage = measure_coverage(repo)

    # 2. Gaps
    result.gap = find_coverage_gaps(result.coverage)

    # 3. Mutation (optional — slow)
    if include_mutation:
        result.mutation = run_mutation(repo, workers=mutation_workers)

    # 4. Untested endpoints (optional)
    if include_endpoints:
        result.endpoints = find_untested_endpoints(repo)

    # 5. Risk
    result.risk = compute_risk(repo, result.coverage)

    # 6. Dashboard
    result.dashboard = build_dashboard_data(
        result.coverage,
        result.gap,
        result.mutation,
        result.risk,
    )

    # 7. Gate
    result.passed_gate = result.coverage.percent >= gate_threshold

    return result
