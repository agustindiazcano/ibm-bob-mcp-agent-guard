"""Measurement history store (docs/DATA_PLATFORM.md, Phase 17).

The engine measures; this package only stores what it measured. It is inert
unless REPOGUARD_DATABASE_URL is set, and this module deliberately imports
nothing from SQLAlchemy: `import repoguard_engine` must keep working without
the optional `[db]` extra. Only store.db / models / views / repository need it,
and pipeline.py imports those lazily, inside the code path that persists.
"""

from __future__ import annotations

import os

DATABASE_URL_ENV = "REPOGUARD_DATABASE_URL"


class StoreError(RuntimeError):
    """Persistence was requested but can't happen (missing extra, bad URL,
    unreachable database, invalid project slug, failed write)."""


def database_url() -> str | None:
    """REPOGUARD_DATABASE_URL, normalized to the psycopg 3 driver, or None if unset."""
    raw = os.environ.get(DATABASE_URL_ENV, "").strip()
    return normalize_url(raw) if raw else None


def is_enabled() -> bool:
    """True when a database URL is configured (persistence defaults on for trusted callers)."""
    return database_url() is not None


def normalize_url(url: str) -> str:
    """Point plain postgres:// / postgresql:// URLs at psycopg 3, the driver
    the `[db]` extra installs (SQLAlchemy's default Postgres driver is
    psycopg2, which isn't a dependency). URLs that name a driver are untouched."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url
