"""Writes: runs (from a validated run record), projects, API tokens and
fix sessions. Stores values exactly as given; computes nothing."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone

import sqlalchemy as sa

from . import models as m
from .record import validate_run_record


class ProjectNotFound(LookupError):
    pass


class RunConflict(ValueError):
    """A run_id that already exists under a different project."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_project_id(conn: sa.Connection, slug: str) -> str | None:
    return conn.execute(sa.select(m.projects.c.id).where(m.projects.c.slug == slug)).scalar_one_or_none()


def create_project(engine: sa.Engine, slug: str, repo_url: str | None = None) -> str:
    """Create a project (or return the existing one's id)."""
    with engine.begin() as conn:
        return _ensure_project(conn, slug, repo_url)


def _ensure_project(conn: sa.Connection, slug: str, repo_url: str | None = None) -> str:
    existing = get_project_id(conn, slug)
    if existing:
        return existing
    project_id = str(uuid.uuid4())
    conn.execute(m.projects.insert().values(id=project_id, slug=slug, repo_url=repo_url, created_at=_now()))
    return project_id


def create_token(engine: sa.Engine, slug: str, label: str | None = None) -> str:
    """Create an ingest/persist token for a project. Returns the plaintext
    once; only its SHA-256 is stored."""
    token = secrets.token_urlsafe(32)
    with engine.begin() as conn:
        project_id = get_project_id(conn, slug)
        if project_id is None:
            raise ProjectNotFound(slug)
        conn.execute(m.api_tokens.insert().values(
            id=str(uuid.uuid4()), project_id=project_id, token_sha256=_hash_token(token),
            label=label, created_at=_now(),
        ))
    return token


def revoke_tokens(engine: sa.Engine, slug: str, label: str | None = None) -> int:
    """Revoke a project's active tokens (all, or only those with label)."""
    with engine.begin() as conn:
        project_id = get_project_id(conn, slug)
        if project_id is None:
            raise ProjectNotFound(slug)
        cond = sa.and_(m.api_tokens.c.project_id == project_id, m.api_tokens.c.revoked_at.is_(None))
        if label is not None:
            cond = sa.and_(cond, m.api_tokens.c.label == label)
        return conn.execute(m.api_tokens.update().where(cond).values(revoked_at=_now())).rowcount


def project_for_token(engine: sa.Engine, token: str) -> str | None:
    """The slug a live (non-revoked) token belongs to, or None."""
    with engine.connect() as conn:
        return conn.execute(
            sa.select(m.projects.c.slug)
            .join(m.api_tokens, m.api_tokens.c.project_id == m.projects.c.id)
            .where(m.api_tokens.c.token_sha256 == _hash_token(token), m.api_tokens.c.revoked_at.is_(None))
        ).scalar_one_or_none()


def save_record(engine: sa.Engine, record: dict, *, project: str | None = None) -> tuple[str, bool]:
    """Store a validated run record in one transaction. project overrides
    record["project"] (ingest takes it from the token, never the body).
    Idempotent on run_id: returns (run_id, created) -- created False when
    that run was already stored for the same project. Raises RunConflict
    if the run_id exists under another project."""
    validate_run_record(record)
    slug = project or record.get("project")
    if not slug:
        raise ValueError("record has no project")
    run_id = record["run_id"]
    with engine.begin() as conn:
        project_id = _ensure_project(conn, slug)
        existing = conn.execute(sa.select(m.runs.c.project_id).where(m.runs.c.id == run_id)).scalar_one_or_none()
        if existing is not None:
            if existing != project_id:
                raise RunConflict(f"run {run_id} belongs to another project")
            return run_id, False

        conn.execute(m.runs.insert().values(
            id=run_id,
            project_id=project_id,
            source=record["source"],
            commit_sha=record.get("commit_sha"),
            branch=record.get("branch"),
            dirty=bool(record.get("dirty")),
            started_at=datetime.fromisoformat(record["started_at"]),
            finished_at=datetime.fromisoformat(record["finished_at"]),
            engine_version=record.get("engine_version") or "0+unknown",
            operators_hash=record.get("operators_hash") or "",
            python_version=record.get("python_version") or "",
            gate_threshold=record["gate_threshold"],
            tests_measured=bool(record.get("tests")),
            status="ok",
        ))
        cov = record["coverage"]
        conn.execute(m.coverage_results.insert().values(
            run_id=run_id, percent=cov["percent"], covered_lines=cov["covered_lines"], total_lines=cov["total_lines"],
        ))
        if cov.get("files"):
            conn.execute(m.file_coverage.insert(), [
                {"run_id": run_id, "file_path": f["file_path"], "missing_count": len(f["missing_lines"]),
                 "missing_lines": f["missing_lines"]}
                for f in cov["files"]
            ])
        mutation = record.get("mutation")
        if mutation is not None:
            conn.execute(m.mutation_results.insert().values(
                run_id=run_id, score=mutation["score"], killed=mutation["killed"],
                survived=mutation["survived"], total=mutation["total"],
            ))
            if mutation.get("mutants"):
                conn.execute(m.mutants.insert(), [
                    {"run_id": run_id, "mutant_index": mu["index"], "fingerprint": mu["fingerprint"],
                     "file_path": mu["file_path"], "function_name": mu["function_name"], "lineno": mu["lineno"],
                     "operator": mu["operator"], "description": mu["description"], "outcome": mu["outcome"]}
                    for mu in mutation["mutants"]
                ])
        if record.get("risk"):
            conn.execute(m.risk_scores.insert(), [
                {"run_id": run_id, "file_path": r["file_path"], "score": r["score"], "rank": r["rank"],
                 "reasons": r.get("reasons", [])}
                for r in record["risk"]
            ])
        if record.get("tests"):
            conn.execute(m.test_results.insert(), [
                {"run_id": run_id, "test_id": t["test_id"], "outcome": t["outcome"], "duration_s": t.get("duration_s", 0.0)}
                for t in record["tests"]
            ])
    return run_id, True


def save_fix_session(
    engine: sa.Engine, *, project: str, before_run_id: str, after_run_id: str, provider: str, model_id: str | None
) -> str:
    """Link a fix loop's before/after runs. The effect (delta, tests added)
    is computed by v_fix_effect, not stored."""
    session_id = str(uuid.uuid4())
    with engine.begin() as conn:
        project_id = get_project_id(conn, project)
        if project_id is None:
            raise ProjectNotFound(project)
        conn.execute(m.fix_sessions.insert().values(
            id=session_id, project_id=project_id, before_run_id=before_run_id, after_run_id=after_run_id,
            provider=provider, model_id=model_id, created_at=_now(),
        ))
    return session_id
