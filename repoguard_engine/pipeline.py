"""Pipeline execution: the ordered measurement steps, and (optionally)
persisting the result to the run-history store.

The only module that orders persistence. store/ is imported lazily, inside
the branch that persists, so `import repoguard_engine` never pulls in the
optional [db] extra.
"""

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
    # Set when the run was persisted (run_id) or a run record was requested
    # (record: the dict save_record() / POST /api/runs take).
    run_id: str | None = None
    record: dict | None = None


def run_pipeline(
    repo_path: str | Path,
    *,
    include_mutation: bool = False,
    include_endpoints: bool = True,
    gate_threshold: float = 80.0,
    mutation_workers: int = 1,
    persist: bool | None = None,
    project: str | None = None,
    source: str = "cli",
    build_record: bool = False,
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
    8. Optionally build a run record and store it

    persist: None = store iff REPOGUARD_DATABASE_URL is set (trusted
    callers: CLI, gate, MCP); True/False forces it. When persisting, the
    database is opened and its schema checked *before* measuring, so a bad
    URL or missing [db] extra fails in milliseconds; a write failure after
    measuring raises (the repoguard-out/ files already exist either way).
    project: slug override (see store.context.resolve_project_slug).
    source: "cli" | "server" | "ci" | "mcp", stored with the run.
    build_record: build result.record even without persisting (--push).
    """
    from . import store

    repo = Path(repo_path)
    result = PipelineResult(repo_path=str(repo), gate_threshold=gate_threshold)
    should_persist = store.is_enabled() if persist is None else persist
    engine = None
    if should_persist:
        url = store.database_url()
        if url is None:
            raise store.StoreNotConfigured(f"persistence requested but {store.DATABASE_URL_ENV} is not set")
        from .store.db import get_engine, init_db

        engine = get_engine(url)
        init_db(engine)
    result.started_at = datetime.now(timezone.utc)

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
    result.finished_at = datetime.now(timezone.utc)

    # 8. Record / persist
    if should_persist or build_record:
        from .store.context import collect_context, resolve_project_slug
        from .store.record import build_run_record

        result.record = build_run_record(
            collect_context(repo),
            project=resolve_project_slug(repo, project),
            source=source,
            started_at=result.started_at,
            finished_at=result.finished_at,
            gate_threshold=gate_threshold,
            coverage=result.coverage,
            mutation=result.mutation,
            risk=result.risk,
        )
    if engine is not None:
        from .store.repository import save_record

        result.run_id, _ = save_record(engine, result.record)

    return result
