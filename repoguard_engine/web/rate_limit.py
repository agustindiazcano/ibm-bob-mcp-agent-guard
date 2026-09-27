"""Rate limiting for the public Autofix endpoint (POST /api/fix).

Replaces the REPOGUARD_FIX_TOKEN gate: instead of requiring a shared secret,
cap how often the endpoint can run, since each call spends real AI-provider
quota/cost. Two windows: a per-IP cap (default 10/hour) and a global cap
(default 1000/day) -- both configurable via env vars so the operator picks
numbers that match their actual budget tolerance, never hardcoded here.

Durable (Postgres/SQLite via REPOGUARD_DATABASE_URL) when a database is
configured -- required for correctness on Cloud Run, which can scale to
multiple instances, so an in-memory counter per instance would silently
multiply the real limit. Falls back to an in-memory per-process counter
when no database is configured, which is fine for local/dev use (a single
process) but not durable across restarts or multiple instances.
"""
from __future__ import annotations

import os
import threading
import time
from collections import deque
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

PER_IP_LIMIT = int(os.environ.get("REPOGUARD_FIX_PER_IP_LIMIT", "10"))
PER_IP_WINDOW_S = 3600
GLOBAL_LIMIT = int(os.environ.get("REPOGUARD_FIX_GLOBAL_LIMIT", "1000"))
GLOBAL_WINDOW_S = 86400

# Safety timeout for the per-IP "run in progress" claim: long enough for a
# real run (a full demo-repo mutation pass measured minutes, not seconds),
# short enough that a crashed worker doesn't lock an IP out forever.
MAX_RUN_MINUTES = int(os.environ.get("REPOGUARD_FIX_MAX_RUN_MINUTES", "20"))

_lock = threading.Lock()
_by_ip: dict[str, deque[float]] = {}
_global: deque[float] = deque()
_active: dict[str, float] = {}  # in-memory fallback for try_claim_run/release_run


def client_ip(x_forwarded_for: str | None, direct_ip: str | None) -> str:
    """The real client IP behind Cloud Run's proxy: the first hop in
    X-Forwarded-For (set by Cloud Run's own load balancer, not spoofable by
    the client past it), falling back to the direct connection IP."""
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return direct_ip or "unknown"


def _prune(dq: deque[float], window_s: float, now: float) -> None:
    while dq and now - dq[0] > window_s:
        dq.popleft()


def _check_memory(ip: str) -> tuple[bool, str]:
    now = time.time()
    with _lock:
        _prune(_global, GLOBAL_WINDOW_S, now)
        if len(_global) >= GLOBAL_LIMIT:
            return False, f"Autofix has hit its global limit of {GLOBAL_LIMIT} runs per day. Try again later."
        ip_dq = _by_ip.setdefault(ip, deque())
        _prune(ip_dq, PER_IP_WINDOW_S, now)
        if len(ip_dq) >= PER_IP_LIMIT:
            return False, f"Autofix allows {PER_IP_LIMIT} runs per hour per IP. Try again later."
        ip_dq.append(now)
        _global.append(now)
        return True, ""


def _check_db(engine, ip: str) -> tuple[bool, str]:
    from sqlalchemy import func, insert, select

    from ..store.models import fix_requests
    now = datetime.now(timezone.utc)
    with engine.begin() as conn:
        global_count = conn.execute(
            select(func.count()).select_from(fix_requests)
            .where(fix_requests.c.created_at > now - timedelta(seconds=GLOBAL_WINDOW_S))
        ).scalar_one()
        if global_count >= GLOBAL_LIMIT:
            return False, f"Autofix has hit its global limit of {GLOBAL_LIMIT} runs per day. Try again later."

        ip_count = conn.execute(
            select(func.count()).select_from(fix_requests)
            .where(fix_requests.c.ip == ip, fix_requests.c.created_at > now - timedelta(seconds=PER_IP_WINDOW_S))
        ).scalar_one()
        if ip_count >= PER_IP_LIMIT:
            return False, f"Autofix allows {PER_IP_LIMIT} runs per hour per IP. Try again later."

        conn.execute(insert(fix_requests).values(ip=ip, created_at=now))
    return True, ""


def check_rate_limit(ip: str) -> None:
    """Raise 429 if this IP or the service overall has hit its Autofix rate
    limit; otherwise record the call and let it through."""
    from .. import store

    url = store.database_url()
    if url:
        from ..store.db import get_engine, init_db

        engine = get_engine(url)
        init_db(engine)
        ok, message = _check_db(engine, ip)
    else:
        ok, message = _check_memory(ip)

    if not ok:
        raise HTTPException(status_code=429, detail=message)


def _claim_memory(ip: str) -> bool:
    now = time.time()
    with _lock:
        started = _active.get(ip)
        if started is not None and now - started < MAX_RUN_MINUTES * 60:
            return False
        _active[ip] = now
        return True


def _release_memory(ip: str) -> None:
    with _lock:
        _active.pop(ip, None)


def _claim_db(engine, ip: str) -> bool:
    from sqlalchemy import delete, insert, select

    from ..store.models import fix_active_runs

    now = datetime.now(timezone.utc)
    stale_before = now - timedelta(minutes=MAX_RUN_MINUTES)
    with engine.begin() as conn:
        conn.execute(delete(fix_active_runs).where(fix_active_runs.c.started_at < stale_before))
        existing = conn.execute(
            select(fix_active_runs.c.ip).where(fix_active_runs.c.ip == ip)
        ).first()
        if existing is not None:
            return False
        conn.execute(insert(fix_active_runs).values(ip=ip, started_at=now))
    return True


def _release_db(engine, ip: str) -> None:
    from sqlalchemy import delete

    from ..store.models import fix_active_runs

    with engine.begin() as conn:
        conn.execute(delete(fix_active_runs).where(fix_active_runs.c.ip == ip))


def try_claim_run(ip: str) -> None:
    """Raise 409 if this IP already has an Autofix run in progress;
    otherwise claim the slot for it. Per-IP, not global -- different
    visitors no longer queue behind whichever one clicked first. Durable via
    the fix_active_runs table when REPOGUARD_DATABASE_URL is set (required
    for correctness: Cloud Run can scale to multiple instances, so an
    in-memory claim per instance wouldn't stop the same IP hitting a
    different, idle instance); an in-memory dict otherwise."""
    from .. import store

    url = store.database_url()
    if url:
        from ..store.db import get_engine, init_db

        engine = get_engine(url)
        init_db(engine)
        claimed = _claim_db(engine, ip)
    else:
        claimed = _claim_memory(ip)

    if not claimed:
        raise HTTPException(status_code=409, detail="You already have an Autofix run in progress; wait for it to finish and try again.")


def release_run(ip: str) -> None:
    """Release this IP's claim so it can start another Autofix run. Called
    from the worker's `finally`, so it runs on success, on error, and even
    if the client disconnects."""
    from .. import store

    url = store.database_url()
    if url:
        from ..store.db import get_engine

        _release_db(get_engine(url), ip)
    else:
        _release_memory(ip)
