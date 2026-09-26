"""FastAPI web server with SSE endpoint for real-time dashboard updates."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

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
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Serve static files (index.html)
_static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serve the web UI."""
    html = (_static_dir / "index.html").read_text()
    return HTMLResponse(content=html)


@app.get("/api/analyze")
async def api_analyze(
    repo_path: str = Query(default=".", description="Path to the target repository"),
    mutation: bool = Query(default=False),
    gate_threshold: float = Query(default=80.0),
) -> dict:
    """Run the full pipeline and return JSON results."""
    from ..pipeline import run_pipeline

    result = run_pipeline(repo_path, include_mutation=mutation, gate_threshold=gate_threshold)
    return {**result.dashboard, "passed_gate": result.passed_gate}


@app.get("/api/stream")
async def api_stream(
    repo_path: str = Query(default=".", description="Path to the target repository"),
) -> StreamingResponse:
    """
    Server-Sent Events stream that emits pipeline progress events.
    Each event is a JSON object with a 'type' and 'data' field.
    """
    return StreamingResponse(
        _stream_pipeline(repo_path),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _stream_pipeline(repo_path: str) -> AsyncGenerator[str, None]:
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

        yield _emit("done", {"passed_gate": coverage.percent >= 80.0})

    except Exception as exc:
        yield _emit("error", {"message": str(exc)})
