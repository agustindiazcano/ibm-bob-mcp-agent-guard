"""Writes run records to the database. Stores only; computes nothing."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from . import StoreError
from .db import _short, describe
from .models import (
    api_tokens,
    coverage_results,
    endpoint_results,
    file_coverage,
    mutants,
    mutation_results,
    projects,
    risk_scores,
    runs,
    test_results,
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
    try:
        with engine.begin() as conn:
            project_id = _get_or_create_project(conn, project, record["context"]["repo_url"])
            _insert_run(conn, project_id, run_id, record, source)
    except SQLAlchemyError as exc:
        raise StoreError(f"could not store run {run_id} in {describe(engine)}: {_short(exc)}") from exc
    return run_id


def ingest_record(engine: Engine, record: dict[str, Any], *, project_slug: str) -> tuple[str, bool]:
    """Store a run record pushed via `POST /api/runs` (Phase 17 A3.2) under
    *project_slug* -- the caller's token project, never a field in *record*.
    Idempotent on the record's own run_id: a repeat post with the same id
    changes nothing and returns (run_id, False); a new one returns
    (run_id, True). Raises ValueError for a malformed record, StoreError if
    the database write fails."""
    validate_run_record(record)
    run_id = record["run_id"]
    try:
        with engine.begin() as conn:
            if conn.execute(select(runs.c.id).where(runs.c.id == run_id)).scalar_one_or_none() is not None:
                return run_id, False
            project_id = _get_or_create_project(conn, project_slug, record["context"]["repo_url"])
            _insert_run(conn, project_id, run_id, record, source="ci")
    except SQLAlchemyError as exc:
        raise StoreError(f"could not store run {run_id} in {describe(engine)}: {_short(exc)}") from exc
    return run_id, True


def create_project(engine: Engine, slug: str, repo_url: str | None = None) -> str:
    """Create *slug* if it doesn't exist yet (idempotent). Returns its id."""
    from .context import _SLUG_RE

    if not _SLUG_RE.match(slug):
        raise StoreError(
            f"invalid project slug: {slug!r} -- use 1-100 lowercase letters, digits, "
            "'.', '_' or '-', starting with a letter or digit"
        )
    try:
        with engine.begin() as conn:
            return _get_or_create_project(conn, slug, repo_url)
    except SQLAlchemyError as exc:
        raise StoreError(f"could not create project {slug!r} in {describe(engine)}: {_short(exc)}") from exc


def create_token(engine: Engine, slug: str, label: str | None = None) -> tuple[str, str]:
    """A new ingest token for *slug*, which must already exist. Returns
    (token_id, plaintext) -- the plaintext is shown once and never stored;
    only its SHA-256 hash is."""
    token = secrets.token_urlsafe(32)
    token_id = str(uuid.uuid4())
    try:
        with engine.begin() as conn:
            project_id = conn.execute(select(projects.c.id).where(projects.c.slug == slug)).scalar_one_or_none()
            if project_id is None:
                raise StoreError(f"no project {slug!r} -- run `repoguard db create-project {slug}` first")
            conn.execute(api_tokens.insert().values(
                id=token_id, project_id=project_id, token_hash=_hash_token(token),
                label=label, created_at=datetime.now(timezone.utc), revoked_at=None,
            ))
    except SQLAlchemyError as exc:
        raise StoreError(f"could not create a token for {slug!r} in {describe(engine)}: {_short(exc)}") from exc
    return token_id, token


def project_for_token(engine: Engine, token: str) -> str | None:
    """The project slug for a live (non-revoked) token, or None."""
    with engine.connect() as conn:
        return conn.execute(
            select(projects.c.slug)
            .select_from(api_tokens.join(projects, api_tokens.c.project_id == projects.c.id))
            .where(api_tokens.c.token_hash == _hash_token(token), api_tokens.c.revoked_at.is_(None))
        ).scalar_one_or_none()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _insert_run(conn: Connection, project_id: str, run_id: str, record: dict[str, Any], source: str) -> None:
    ctx = record["context"]
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
        tests_measured=True,  # coverage.tests is always measured (§4.1)
        status=record["status"],
        error=record["error"],
    ))
    _insert_measurements(conn, run_id, record)


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

    rows = [
        {"run_id": run_id, "mutant_index": m["index"], "fingerprint": m["fingerprint"],
         "file_path": m["file"], "function_name": m["function"], "lineno": m["lineno"],
         "operator": m["operator"], "description": m["description"], "outcome": m["outcome"]}
        for m in (record["mutants"] or [])
    ]
    if rows:
        conn.execute(mutants.insert(), rows)

    rows = [
        {"run_id": run_id, "test_id": t["test_id"], "outcome": t["outcome"], "duration_s": t["duration_s"]}
        for t in record["tests"]
    ]
    if rows:
        conn.execute(test_results.insert(), rows)


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
