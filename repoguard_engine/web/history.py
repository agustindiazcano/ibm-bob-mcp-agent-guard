"""Run-history API: read routes over store/queries.py, CI ingest
(POST /api/runs) and the project-token check /api/analyze?persist=true uses.

Thin by design: every value comes from a stored measurement or a SQL view;
nothing is computed here. Without REPOGUARD_DATABASE_URL every route
answers 503 "persistence not configured", so the dashboard can tell "no
database" apart from "no runs yet" (an empty list).
"""

from __future__ import annotations

from fastapi import APIRouter, Body, Header, HTTPException, Query
from fastapi.responses import JSONResponse

from .. import store

router = APIRouter()
_initialized: set[str] = set()


def store_engine():
    """The configured engine, schema/views created once per URL per
    process. 503 when persistence isn't configured or [db] is missing."""
    url = store.database_url()
    if url is None:
        raise HTTPException(status_code=503, detail="persistence not configured")
    try:
        from ..store.db import get_engine, init_db
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="persistence not configured: the [db] extra is not installed") from exc
    engine = get_engine(url)
    if url not in _initialized:
        init_db(engine)
        _initialized.add(url)
    return engine


def project_from_token(engine, authorization: str | None) -> str:
    """The project a bearer token belongs to; 401 if missing/unknown/revoked."""
    from ..store.repository import project_for_token

    scheme, _, token = (authorization or "").partition(" ")
    slug = project_for_token(engine, token.strip()) if scheme.lower() == "bearer" and token.strip() else None
    if slug is None:
        raise HTTPException(status_code=401, detail="Missing, unknown or revoked project token.")
    return slug


def _read(fn, slug: str, **kwargs) -> list[dict]:
    from ..store.repository import ProjectNotFound

    engine = store_engine()
    try:
        return fn(engine, slug, **kwargs)
    except ProjectNotFound:
        raise HTTPException(status_code=404, detail=f"unknown project: {slug}") from None


@router.get("/api/projects")
def api_projects() -> list[dict]:
    from ..store.queries import list_projects

    return list_projects(store_engine())


@router.get("/api/projects/{slug}/runs")
def api_runs(slug: str, limit: int = Query(default=50, ge=1, le=500)) -> list[dict]:
    from ..store.queries import list_runs

    return _read(list_runs, slug, limit=limit)


@router.get("/api/projects/{slug}/trend")
def api_trend(slug: str) -> list[dict]:
    from ..store.queries import trend

    return _read(trend, slug)


@router.get("/api/projects/{slug}/operators")
def api_operators(slug: str) -> list[dict]:
    from ..store.queries import operators

    return _read(operators, slug)


@router.get("/api/projects/{slug}/risk-heatmap")
def api_risk_heatmap(slug: str, runs: int = Query(default=20, ge=1, le=200)) -> list[dict]:
    from ..store.queries import risk_heatmap

    return _read(risk_heatmap, slug, runs=runs)


@router.get("/api/projects/{slug}/fix-effect")
def api_fix_effect(slug: str) -> list[dict]:
    from ..store.queries import fix_effect

    return _read(fix_effect, slug)


@router.get("/api/projects/{slug}/survivors")
def api_survivors(slug: str) -> list[dict]:
    from ..store.queries import survivors

    return _read(survivors, slug)


@router.get("/api/projects/{slug}/flaky")
def api_flaky(slug: str) -> list[dict]:
    from ..store.queries import flaky

    return _read(flaky, slug)


@router.post("/api/runs")
def api_ingest_run(record: dict = Body(...), authorization: str | None = Header(default=None)) -> JSONResponse:
    """Store a run measured elsewhere (CI, `repoguard analyze --push`).
    The project comes from the token, never the body; the record is
    validated but never recomputed. Same run_id again -> 200 with the same
    id (idempotent retry); new -> 201."""
    from ..store.record import RecordError
    from ..store.repository import RunConflict, save_record

    engine = store_engine()
    slug = project_from_token(engine, authorization)
    record = {**record, "source": "ci"} if record.get("source") != "ci" else record
    try:
        run_id, created = save_record(engine, record, project=slug)
    except RecordError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RunConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return JSONResponse({"run_id": run_id, "project": slug}, status_code=201 if created else 200)
