"""Pipeline execution: measure mode and bob-fix mode."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
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
from . import store


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
    started_at: datetime | None = None
    finished_at: datetime | None = None
    run_id: str | None = None     # set only when the run was stored
    project: str | None = None    # project slug the run was stored under


def run_pipeline(
    repo_path: str | Path,
    *,
    include_mutation: bool = False,
    include_endpoints: bool = True,
    gate_threshold: float = 80.0,
    persist: bool | None = None,
    project: str | None = None,
) -> PipelineResult:
    """
    Full measurement pipeline.

    persist=None stores the run iff REPOGUARD_DATABASE_URL is set -- the
    default for trusted callers (CLI, MCP). Public/indirect callers (the web
    server, the fix loop) pass persist=False explicitly. When persisting, the
    database is checked *before* measuring, so a missing [db] extra, a bad
    URL or an unreachable database raises store.StoreError in milliseconds
    instead of after minutes of mutation testing. A failed write after
    measuring also raises (DATA_PLATFORM.md §13, decision #2); the
    repoguard-out/*.json files are already written by then. Storing never
    changes a measured number or an output file.

    Steps:
    1. Run pytest + coverage
    2. Derive gap report
    3. Optionally run mutation testing (own AST engine)
    4. Optionally detect untested FastAPI endpoints
    5. Compute risk scores
    6. Assemble dashboard data
    7. Evaluate gate threshold
    8. Optionally store the run (store/, Phase 17)
    """
    repo = Path(repo_path)
    result = PipelineResult(repo_path=str(repo), gate_threshold=gate_threshold)

    if persist is None:
        persist = store.is_enabled()
    target = _open_store(repo, project) if persist else None
    result.started_at = datetime.now(timezone.utc)

    # 1. Coverage
    result.coverage = measure_coverage(repo)

    # 2. Gaps
    result.gap = find_coverage_gaps(result.coverage)

    # 3. Mutation (optional — slow)
    if include_mutation:
        result.mutation = run_mutation(repo)

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
    result.finished_at = datetime.now(timezone.utc)

    # 8. Store (optional)
    if target is not None:
        _save(target, result, include_endpoints)

    return result


def _open_store(repo: Path, project: str | None) -> tuple:
    """Fail-fast half of persistence: engine + schema + git context, before measuring."""
    url = store.database_url()
    if url is None:
        raise store.StoreError(f"persist=True but {store.DATABASE_URL_ENV} is not set")
    from .store.context import collect_context
    from .store.db import get_engine, init_db

    engine = get_engine(url)
    init_db(engine)
    return engine, collect_context(repo, project)


def _save(target: tuple, result: PipelineResult, include_endpoints: bool) -> None:
    from .store.record import build_run_record, new_run_id
    from .store.repository import save_record

    engine, ctx = target
    try:
        record = build_run_record(
            ctx,
            run_id=new_run_id(),
            started_at=result.started_at,
            finished_at=result.finished_at,
            gate_threshold=result.gate_threshold,
            coverage=result.coverage,
            mutation=result.mutation,
            risk=result.risk,
            endpoints=result.endpoints if include_endpoints else None,
        )
    except ValueError as exc:  # e.g. the wall clock stepped back during a long run
        raise store.StoreError(f"measured, but the run record was rejected: {exc}") from exc
    result.run_id = save_record(engine, record, project=ctx.project, source="cli")
    result.project = ctx.project
