"""Read-only queries for measurement history. Reads only; never computes a
derived value here (that's what store/views.py's SQL views are for)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, select, text

from .models import endpoint_results, projects, risk_scores, runs

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

# v_run_trend has no SQLAlchemy Table (it's a raw-DDL view -- store/views.py),
# so a plain text() query gets the driver's own value for started_at (a str
# on SQLite, a real datetime on Postgres) instead of a converted Python type.
# .columns() tells SQLAlchemy to apply DateTime's result processing either way.
_TREND_QUERY = text(
    "SELECT run_id, commit_sha, started_at, operators_hash, coverage_pct, "
    "mutation_pct, coverage_minus_mutation_pp, passed_gate "
    "FROM v_run_trend WHERE project_id = :project_id ORDER BY started_at"
).columns(started_at=DateTime(timezone=True))

# Latest-run-only view (Phase 17 A2-gap); one row per mutation operator.
_SURVIVAL_BY_OPERATOR_QUERY = text(
    "SELECT operator, total, survived, survival_pct "
    "FROM v_survival_by_operator WHERE project_id = :project_id ORDER BY survival_pct DESC"
)

# Sorted by runs_seen (docs/DATA_PLATFORM.md §6 chart 5): the longest-standing gaps first.
_PERSISTENT_SURVIVORS_QUERY = text(
    "SELECT fingerprint, file_path, function_name, description, runs_seen, first_seen "
    "FROM v_persistent_survivors WHERE project_id = :project_id ORDER BY runs_seen DESC"
).columns(first_seen=DateTime(timezone=True))

_FLAKY_TESTS_QUERY = text(
    "SELECT commit_sha, test_id, distinct_outcomes, runs "
    "FROM v_flaky_tests WHERE project_id = :project_id ORDER BY commit_sha, test_id"
)


def list_projects(engine: Engine) -> list[dict[str, Any]]:
    """Every known project, newest first."""
    with engine.connect() as conn:
        rows = conn.execute(
            select(projects.c.slug, projects.c.repo_url, projects.c.created_at)
            .order_by(projects.c.created_at.desc())
        ).mappings().all()
        return [{"slug": r["slug"], "repo_url": r["repo_url"], "created_at": r["created_at"].isoformat()} for r in rows]


def trend(engine: Engine, project_slug: str) -> list[dict[str, Any]] | None:
    """v_run_trend rows for *project_slug*, oldest first (chart-ready order).
    None if the project doesn't exist."""
    with engine.connect() as conn:
        project_id = conn.execute(select(projects.c.id).where(projects.c.slug == project_slug)).scalar_one_or_none()
        if project_id is None:
            return None
        rows = conn.execute(_TREND_QUERY, {"project_id": project_id}).mappings().all()
        return [
            {**dict(r), "started_at": r["started_at"].isoformat()}
            for r in rows
        ]


def survival_by_operator(engine: Engine, project_slug: str) -> list[dict[str, Any]] | None:
    """Which mutation operators the suite misses most, from *project_slug*'s
    latest run only (v_survival_by_operator). None if the project doesn't
    exist. An empty list means the project exists but mutation was never
    measured -- distinct from "no such project"."""
    with engine.connect() as conn:
        project_id = conn.execute(select(projects.c.id).where(projects.c.slug == project_slug)).scalar_one_or_none()
        if project_id is None:
            return None
        rows = conn.execute(_SURVIVAL_BY_OPERATOR_QUERY, {"project_id": project_id}).mappings().all()
        return [dict(r) for r in rows]


def persistent_survivors(engine: Engine, project_slug: str) -> list[dict[str, Any]] | None:
    """Mutants that have never been killed across every non-dirty run of
    *project_slug* (v_persistent_survivors), oldest-seen first. None if the
    project doesn't exist."""
    with engine.connect() as conn:
        project_id = conn.execute(select(projects.c.id).where(projects.c.slug == project_slug)).scalar_one_or_none()
        if project_id is None:
            return None
        rows = conn.execute(_PERSISTENT_SURVIVORS_QUERY, {"project_id": project_id}).mappings().all()
        return [{**dict(r), "first_seen": r["first_seen"].isoformat()} for r in rows]


def flaky_tests(engine: Engine, project_slug: str) -> list[dict[str, Any]] | None:
    """Tests whose outcome varied across non-dirty runs of the same commit
    for *project_slug* (v_flaky_tests). None if the project doesn't exist.
    Usually empty -- flakiness needs 2+ runs on the same commit_sha."""
    with engine.connect() as conn:
        project_id = conn.execute(select(projects.c.id).where(projects.c.slug == project_slug)).scalar_one_or_none()
        if project_id is None:
            return None
        rows = conn.execute(_FLAKY_TESTS_QUERY, {"project_id": project_id}).mappings().all()
        return [dict(r) for r in rows]


def risk_heatmap(engine: Engine, project_slug: str) -> list[dict[str, Any]] | None:
    """risk_scores from *project_slug*'s most recent run that measured
    coverage, ordered by rank. None if the project doesn't exist or has no
    runs yet."""
    with engine.connect() as conn:
        project_id = conn.execute(select(projects.c.id).where(projects.c.slug == project_slug)).scalar_one_or_none()
        if project_id is None:
            return None
        run_id = conn.execute(
            select(runs.c.id)
            .where(runs.c.project_id == project_id, runs.c.status == "ok")
            .order_by(runs.c.started_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if run_id is None:
            return None
        rows = conn.execute(
            select(risk_scores.c.file_path, risk_scores.c.score, risk_scores.c.rank, risk_scores.c.reasons)
            .where(risk_scores.c.run_id == run_id)
            .order_by(risk_scores.c.rank)
        ).mappings().all()
        return [dict(r) for r in rows]


def latest_endpoints(engine: Engine, project_slug: str) -> list[dict[str, Any]] | None:
    """Endpoint coverage from *project_slug*'s most recent run with endpoints
    measured, ordered as the engine emitted them. None if the project doesn't
    exist yet, or exists but no run has ever measured endpoints."""
    with engine.connect() as conn:
        project_id = conn.execute(
            select(projects.c.id).where(projects.c.slug == project_slug)
        ).scalar_one_or_none()
        if project_id is None:
            return None

        run_id = conn.execute(
            select(runs.c.id)
            .where(runs.c.project_id == project_id, runs.c.endpoints_measured.is_(True))
            .order_by(runs.c.started_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if run_id is None:
            return None

        rows = conn.execute(
            select(endpoint_results)
            .where(endpoint_results.c.run_id == run_id)
            .order_by(endpoint_results.c.ordinal)
        ).mappings().all()
        return [
            {
                "file": row["file_path"],
                "function": row["function_name"],
                "method": row["method"],
                "path": row["path"],
                "has_test": row["has_test"],
            }
            for row in rows
        ]
