"""Writes run records to the database. Stores only; computes nothing."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from . import StoreError
from .db import _short, describe
from .models import (
    coverage_results, endpoint_results, file_coverage, mutation_results,
    projects, risk_scores, runs,
)
from .record import validate_run_record

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection, Engine

SOURCES = ("cli", "server", "ci")


def save_record(engine: Engine, record: dict[str, Any], *, project: str, source: str) -> str:
    """Store one validated run record under *project* (created if new), in a
    single transaction. Returns the run id. Raises ValueError for a malformed
    record, StoreError if the database write fails."""
    validate_run_record(record)
    if source not in SOURCES:
        raise ValueError(f"source must be one of {SOURCES}, got {source!r}")

    run_id = record["run_id"]
    ctx = record["context"]
    try:
        with engine.begin() as conn:
            project_id = _get_or_create_project(conn, project, ctx["repo_url"])
            conn.execute(runs.insert().values(
                id=run_id,
                project_id=project_id,
                source=source,
                commit_sha=ctx["commit_sha"],
                branch=ctx["branch"],
                dirty=ctx["dirty"],
                started_at=datetime.fromisoformat(record["started_at"]),
                finished_at=datetime.fromisoformat(record["finished_at"]),
                engine_version=ctx["engine_version"],
                operators_hash=ctx["operators_hash"],
                python_version=ctx["python_version"],
                gate_threshold=record["gate_threshold"],
                endpoints_measured=record["endpoints"] is not None,
                tests_measured=False,  # per-test outcomes arrive with Phase 17 A2.2
                status=record["status"],
                error=record["error"],
            ))
            _insert_measurements(conn, run_id, record)
    except SQLAlchemyError as exc:
        raise StoreError(f"could not store run {run_id} in {describe(engine)}: {_short(exc)}") from exc
    return run_id


def _insert_measurements(conn: Connection, run_id: str, record: dict[str, Any]) -> None:
    cov = record["coverage"]
    if cov is not None:
        conn.execute(coverage_results.insert().values(
            run_id=run_id, percent=cov["percent"],
            covered_lines=cov["covered_lines"], total_lines=cov["total_lines"],
        ))
        rows = [
            {"run_id": run_id, "file_path": path, "missing_count": len(lines), "missing_lines": lines}
            for path, lines in cov["missing_lines"].items()
        ]
        if rows:
            conn.execute(file_coverage.insert(), rows)

    mut = record["mutation"]
    if mut is not None:
        conn.execute(mutation_results.insert().values(run_id=run_id, **mut))

    rows = [
        {"run_id": run_id, "file_path": r["file"], "score": r["score"], "rank": r["rank"], "reasons": r["reasons"]}
        for r in record["risk"]
    ]
    if rows:
        conn.execute(risk_scores.insert(), rows)

    rows = [
        {"run_id": run_id, "ordinal": i, "file_path": e["file"], "function_name": e["function"],
         "method": e["method"], "path": e["path"], "has_test": e["has_test"]}
        for i, e in enumerate(record["endpoints"] or [])
    ]
    if rows:
        conn.execute(endpoint_results.insert(), rows)


def _get_or_create_project(conn: Connection, slug: str, repo_url: str | None) -> str:
    # INSERT ... ON CONFLICT DO NOTHING exists on both backends; a concurrent
    # writer creating the same slug first just makes this insert a no-op.
    if conn.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    conn.execute(
        insert(projects)
        .values(id=str(uuid.uuid4()), slug=slug, repo_url=repo_url, created_at=datetime.now(timezone.utc))
        .on_conflict_do_nothing(index_elements=["slug"])
    )
    return conn.execute(select(projects.c.id).where(projects.c.slug == slug)).scalar_one()
