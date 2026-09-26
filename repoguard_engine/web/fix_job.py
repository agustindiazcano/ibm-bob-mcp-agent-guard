"""Autofix over HTTP: run the AI fix loop on a throwaway copy of a repo and
stream its progress as NDJSON.

Backs POST /api/fix (web/server.py). Three rules the CLI's `repoguard fix`
doesn't need but an HTTP endpoint does:

- Token-gated. REPOGUARD_FIX_TOKEN unset -> the endpoint is off (503); a
  missing or wrong `Authorization: Bearer <token>` -> 401. Each run spends
  AI-provider quota for minutes, and the deployed service is public.
- One run at a time per process (409 otherwise).
- Never touches the target repo. The loop runs on a temp copy, never
  publishes (no git/gh), and the copy is deleted afterwards; the tests it
  wrote come back in the final `done` event instead.

Every number in the stream is an engine measurement (pipeline.run_pipeline
via run_fix_loop); nothing here computes or estimates a metric.
"""

from __future__ import annotations

import hmac
import json
import os
import queue
import shutil
import tempfile
import threading
from pathlib import Path
from typing import Iterator

from fastapi import HTTPException

_run_lock = threading.Lock()
_HEARTBEAT_SECONDS = 15
_COPY_IGNORE = shutil.ignore_patterns(
    ".git", "repoguard-out", "watson-evidence", "__pycache__", ".pytest_cache",
    ".venv", "node_modules", ".coverage", "coverage.json",
)


def check_token(authorization: str | None) -> None:
    """Raise 503 if Autofix is disabled on this server, 401 if the bearer
    token is missing or wrong."""
    expected = os.environ.get("REPOGUARD_FIX_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Autofix is disabled on this server (REPOGUARD_FIX_TOKEN is not set).")
    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(supplied.strip().encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Missing or invalid Autofix token.")


def start_fix_stream(repo_path: str, gate_threshold: float, provider: str | None) -> Iterator[str]:
    """Claim the single run slot, start the fix loop on a sandbox copy in a
    worker thread, and return an NDJSON line iterator over its events.

    Raises 409 if a run is already in progress. The worker (not the
    iterator) owns the slot, so it is released even if the client
    disconnects before reading anything.
    """
    if not _run_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="An Autofix run is already in progress on this server; try again when it finishes.")
    events: queue.Queue[dict | None] = queue.Queue()
    try:
        worker = threading.Thread(
            target=_run, args=(repo_path, gate_threshold, provider, events), daemon=True, name="repoguard-fix"
        )
        worker.start()
    except BaseException:
        _run_lock.release()
        raise
    return _drain(events)


def _drain(events: "queue.Queue[dict | None]") -> Iterator[str]:
    """Yield one JSON line per event until the worker signals the end.
    Heartbeats keep an idle connection (a multi-minute mutation run emits
    nothing) from looking dead to the client or a proxy."""
    while True:
        try:
            event = events.get(timeout=_HEARTBEAT_SECONDS)
        except queue.Empty:
            event = {"type": "heartbeat", "data": {}}
        if event is None:
            return
        yield json.dumps(event, default=str) + "\n"


def _run(repo_path: str, gate_threshold: float, provider: str | None, events: "queue.Queue[dict | None]") -> None:
    """Worker body: copy, run the loop, report the tests it wrote, clean up."""
    from ..ai_providers import resolve_provider_name
    from ..watson_agent import run_fix_loop

    def emit(event_type: str, data: dict) -> None:
        events.put({"type": event_type, "data": data})

    original = Path(repo_path).resolve()
    sandbox = None
    try:
        sandbox = Path(tempfile.mkdtemp(prefix="repoguard-fix-"))
        work = sandbox / original.name
        shutil.copytree(original, work, ignore=_COPY_IGNORE)
        resolved_provider = resolve_provider_name(provider)
        emit("start", {"repo_path": str(original), "provider": resolved_provider})

        result = run_fix_loop(
            str(work), gate_threshold=gate_threshold, publish=False, provider=provider, on_event=emit
        )
        evidence = Path(result.evidence_path).read_text(encoding="utf-8") if result.evidence_path else ""
        emit(
            "done",
            {
                "provider": resolved_provider,
                "before": result.baseline,
                "after": result.after,
                "files_attempted": result.files_attempted,
                "files": _changed_tests(original, work),
                "critic_notes": result.critic_notes,
                "evidence": evidence,
            },
        )
    except Exception as exc:
        emit("error", {"message": f"{type(exc).__name__}: {exc}"})
    finally:
        if sandbox is not None:
            shutil.rmtree(sandbox, ignore_errors=True)
        _run_lock.release()
        events.put(None)


def _changed_tests(original: Path, work: Path) -> list[dict]:
    """Test files the loop added or changed in the sandbox, relative to the
    repo root, with their full content."""
    changed = []
    tests_dir = work / "tests"
    if not tests_dir.is_dir():
        return changed
    for path in sorted(tests_dir.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(work)
        before = original / rel
        content = path.read_text(encoding="utf-8")
        if not before.exists():
            changed.append({"path": rel.as_posix(), "status": "added", "content": content})
        elif before.read_text(encoding="utf-8") != content:
            changed.append({"path": rel.as_posix(), "status": "modified", "content": content})
    return changed
