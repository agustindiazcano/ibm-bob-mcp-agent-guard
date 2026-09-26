"""Read-only queries for measurement history. Reads only; never computes a
derived value here (that's what store/views.py's SQL views are for)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from .models import endpoint_results, projects, runs

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


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
