"""FastAPI web server with SSE endpoint for real-time dashboard updates."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Header, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="RepoGuard Dashboard", version="0.1.0")

# Frontend origins allowed to call this API (e.g. the web-next dev server and
# its Vercel deployment). Comma-separated; override with REPOGUARD_CORS_ORIGINS.
_default_origins = "http://localhost:3000,http://127.0.0.1:3000"
_allowed_origins = [
    origin.strip()
    for origin in os.environ.get("REPOGUARD_CORS_ORIGINS", _default_origins).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Serve static files (index.html)
_static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serve the web UI."""
    html = (_static_dir / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)


@app.get("/api/analyze")
def api_analyze(
    repo_path: str = Query(default=".", description="Path to the target repository"),
    mutation: bool = Query(default=False),
    gate_threshold: float = Query(default=80.0),
) -> dict:
    """Run the full pipeline and return JSON results."""
    from ..pipeline import run_pipeline

    try:
        # Never stored from here, even with REPOGUARD_DATABASE_URL set: this is a
        # public, unauthenticated route taking an arbitrary server-side path.
        # Web writes wait for per-project tokens (DATA_PLATFORM.md §13, decision #5).
        result = run_pipeline(
            repo_path, include_mutation=mutation, gate_threshold=gate_threshold, persist=False,
        )
    except NotADirectoryError as exc:
        # Otherwise this reaches subprocess.run(cwd=...) uncaught and the
        # frontend sees a bare 500 for what is really a bad request.
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    # run_pipeline already measured the endpoints; they're not part of the
    # dashboard dict (which /api/summary and /api/fix also use), so they're
    # added here instead.
    endpoints = [asdict(ep) for ep in result.endpoints]
    return {**result.dashboard, "endpoints": endpoints, "passed_gate": result.passed_gate}


def _history_engine():
    """The store engine for a read/ingest route, schema guaranteed to exist.
    Raises 503 if no database is configured or it can't be reached -- the
    frontend tells that apart from "no runs yet" ([]), per DATA_PLATFORM.md
    §13 step A3.1."""
    from .. import store
    from ..store.db import get_engine, init_db

    url = store.database_url()
    if url is None:
        raise HTTPException(status_code=503, detail="Run history isn't configured on this backend: it has no database.")
    try:
        engine = get_engine(url)
        init_db(engine)  # idempotent; a fresh database has no tables yet
        return engine
    except store.StoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/projects")
def api_projects() -> list[dict]:
    """Every project with at least one persisted run (Phase 17 A3.1)."""
    from ..store.queries import list_projects

    return list_projects(_history_engine())


@app.get("/api/projects/{slug}/endpoints")
def api_project_endpoints(slug: str) -> list[dict]:
    """Endpoint coverage from *slug*'s most recently measured run. The first
    reader of `store.endpoint_results` (Phase 17 A1-gap) -- everything else
    persisted since Phase 17 A1 already has one (dashboard JSON, /api/analyze,
    or a SQL view), this table didn't."""
    from ..store.queries import latest_endpoints

    result = latest_endpoints(_history_engine(), slug)
    if result is None:
        raise HTTPException(status_code=404, detail=f"no measured endpoints for project {slug!r}")
    return result


@app.get("/api/projects/{slug}/trend")
def api_project_trend(slug: str) -> list[dict]:
    """v_run_trend for *slug*, oldest first (Phase 17 A3.1, chart 1)."""
    from ..store.queries import trend

    result = trend(_history_engine(), slug)
    if result is None:
        raise HTTPException(status_code=404, detail=f"no project {slug!r}")
    return result


@app.get("/api/projects/{slug}/risk-heatmap")
def api_project_risk_heatmap(slug: str) -> list[dict]:
    """risk_scores from *slug*'s most recent run (Phase 17 A3.1, chart 3)."""
    from ..store.queries import risk_heatmap

    result = risk_heatmap(_history_engine(), slug)
    if result is None:
        raise HTTPException(status_code=404, detail=f"no measured run for project {slug!r}")
    return result


@app.post("/api/runs")
def api_ingest_run(record: dict, response: Response, authorization: str | None = Header(default=None)) -> dict:
    """Ingest a run record from a trusted CI caller (Phase 17 A3.2). The
    bearer token identifies the project -- never a field in the body, so a
    token for one project can't write another's history. Idempotent on the
    record's own run_id: a repeat post with the same id changes nothing and
    returns 200; a new one returns 201."""
    from ..store import StoreError
    from ..store.repository import ingest_record, project_for_token

    engine = _history_engine()
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Missing or invalid bearer token.")
    try:
        slug = project_for_token(engine, token.strip())
    except StoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if slug is None:
        raise HTTPException(status_code=401, detail="Missing or invalid bearer token.")

    try:
        run_id, created = ingest_record(engine, record, project_slug=slug)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except StoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    response.status_code = 201 if created else 200
    return {"run_id": run_id, "project": slug}


@app.post("/api/summary")
def api_summary(dashboard: dict) -> dict:
    """Wrap narrative.generate_summary() over an already-measured dashboard dict."""
    from ..narrative import generate_summary

    result = generate_summary(dashboard)
    return {"ok": result.ok, "text": result.text, "error": result.error, "provider": result.provider}


class FixRequest(BaseModel):
    repo_path: str = "."
    gate_threshold: float = 80.0
    provider: str | None = None


@app.post("/api/fix")
def api_fix(body: FixRequest, authorization: str | None = Header(default=None)) -> StreamingResponse:
    """Run the AI fix loop on a sandbox copy of repo_path, streaming NDJSON
    progress events and a final `done` (or `error`) event. Token-gated, one
    run at a time, never modifies repo_path -- see web/fix_job.py."""
    from .fix_job import check_token, start_fix_stream

    check_token(authorization)
    if not Path(body.repo_path).is_dir():
        raise HTTPException(status_code=400, detail=f"repo_path does not exist or is not a directory: {body.repo_path}")
    return StreamingResponse(
        start_fix_stream(body.repo_path, body.gate_threshold, body.provider),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/stream")
async def api_stream(
    repo_path: str = Query(default=".", description="Path to the target repository"),
    gate_threshold: float = Query(default=80.0),
) -> StreamingResponse:
    """
    Server-Sent Events stream that emits pipeline progress events.
    Each event is a JSON object with a 'type' and 'data' field.
    """
    return StreamingResponse(
        _stream_pipeline(repo_path, gate_threshold),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _stream_pipeline(repo_path: str, gate_threshold: float = 80.0) -> AsyncGenerator[str, None]:
    """Yield SSE events as the pipeline progresses."""
    def _emit(event_type: str, data: dict) -> str:
        return f"data: {json.dumps({'type': event_type, 'data': data})}\n\n"

    yield _emit("start", {"repo_path": repo_path})
    await asyncio.sleep(0)

    try:
        from ..core import measure_coverage, find_coverage_gaps, compute_risk
        from ..pipeline import run_pipeline

        # Step 1 — coverage
        yield _emit("progress", {"step": "coverage", "message": "Running pytest with coverage…"})
        await asyncio.sleep(0)
        coverage = await asyncio.get_event_loop().run_in_executor(
            None, measure_coverage, repo_path
        )
        yield _emit("coverage", {"percent": coverage.percent, "total_lines": coverage.total_lines})

        # Step 2 — gaps
        yield _emit("progress", {"step": "gaps", "message": "Computing coverage gaps…"})
        await asyncio.sleep(0)
        gap = find_coverage_gaps(coverage)
        yield _emit("gaps", {"uncovered_files": gap.uncovered_files})

        # Step 3 — risk
        yield _emit("progress", {"step": "risk", "message": "Scoring risk…"})
        await asyncio.sleep(0)
        risk = compute_risk(repo_path, coverage)
        yield _emit("risk", {"top_files": [{"file": r.file, "score": r.score} for r in risk[:5]]})

        yield _emit("done", {"passed_gate": coverage.percent >= gate_threshold})

    except Exception as exc:
        yield _emit("error", {"message": str(exc)})
