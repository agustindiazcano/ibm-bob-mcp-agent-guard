"""Reads, one function per API route. Each is a SELECT from a view or
table; no arithmetic happens in Python. Rows come back as JSON-ready dicts
(datetimes as ISO strings)."""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa

from .repository import ProjectNotFound, get_project_id


def _rows(conn: sa.Connection, sql: str, **params) -> list[dict]:
    out = []
    for row in conn.execute(sa.text(sql), params).mappings():
        out.append({k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in row.items()})
    return out


def _project(conn: sa.Connection, slug: str) -> str:
    project_id = get_project_id(conn, slug)
    if project_id is None:
        raise ProjectNotFound(slug)
    return project_id


def list_projects(engine: sa.Engine) -> list[dict]:
    with engine.connect() as conn:
        return _rows(conn, """
            SELECT p.slug, p.repo_url, p.created_at, COUNT(r.id) AS runs, MAX(r.started_at) AS last_run_at
            FROM projects p LEFT JOIN runs r ON r.project_id = p.id
            GROUP BY p.slug, p.repo_url, p.created_at
            ORDER BY p.slug
        """)


def list_runs(engine: sa.Engine, slug: str, limit: int = 50) -> list[dict]:
    with engine.connect() as conn:
        _project(conn, slug)
        return _rows(conn, "SELECT * FROM v_runs WHERE project = :slug ORDER BY started_at DESC LIMIT :limit",
                     slug=slug, limit=limit)


def trend(engine: sa.Engine, slug: str) -> list[dict]:
    with engine.connect() as conn:
        pid = _project(conn, slug)
        return _rows(conn, """
            SELECT run_id, commit_sha, started_at, operators_hash, coverage_pct, mutation_pct,
                   coverage_minus_mutation_pp, passed_gate
            FROM v_run_trend WHERE project_id = :pid ORDER BY started_at
        """, pid=pid)


def operators(engine: sa.Engine, slug: str) -> list[dict]:
    with engine.connect() as conn:
        pid = _project(conn, slug)
        return _rows(conn, """
            SELECT operator, total, survived, survival_pct FROM v_survival_by_operator
            WHERE project_id = :pid ORDER BY survival_pct DESC, operator
        """, pid=pid)


def risk_heatmap(engine: sa.Engine, slug: str, runs: int = 20) -> list[dict]:
    with engine.connect() as conn:
        pid = _project(conn, slug)
        return _rows(conn, """
            SELECT r.id AS run_id, r.started_at, r.commit_sha, rs.file_path, rs.score, rs.rank
            FROM risk_scores rs
            JOIN runs r ON r.id = rs.run_id
            WHERE r.id IN (
                SELECT id FROM runs WHERE project_id = :pid AND status = 'ok' ORDER BY started_at DESC LIMIT :runs
            )
            ORDER BY r.started_at, rs.rank
        """, pid=pid, runs=runs)


def fix_effect(engine: sa.Engine, slug: str) -> list[dict]:
    with engine.connect() as conn:
        pid = _project(conn, slug)
        return _rows(conn, """
            SELECT id, provider, model_id, created_at, before_run_id, after_run_id,
                   before_pct, after_pct, delta_pp, tests_added
            FROM v_fix_effect WHERE project_id = :pid ORDER BY created_at
        """, pid=pid)


def survivors(engine: sa.Engine, slug: str) -> list[dict]:
    with engine.connect() as conn:
        pid = _project(conn, slug)
        return _rows(conn, """
            SELECT fingerprint, file_path, function_name, lineno, description, runs_seen, first_seen
            FROM v_persistent_survivors WHERE project_id = :pid
            ORDER BY runs_seen DESC, file_path, lineno
        """, pid=pid)


def flaky(engine: sa.Engine, slug: str) -> list[dict]:
    with engine.connect() as conn:
        pid = _project(conn, slug)
        return _rows(conn, """
            SELECT commit_sha, test_id, distinct_outcomes, runs FROM v_flaky_tests
            WHERE project_id = :pid ORDER BY commit_sha, test_id
        """, pid=pid)
