"""Engine creation and schema/view setup."""

from __future__ import annotations

import functools

import sqlalchemy as sa

from .models import metadata
from .views import VIEW_ORDER, VIEWS


@functools.lru_cache(maxsize=8)
def get_engine(url: str) -> sa.Engine:
    """One pooled engine per URL for the process."""
    engine = sa.create_engine(url, future=True, pool_pre_ping=True)
    if engine.dialect.name == "sqlite":
        @sa.event.listens_for(engine, "connect")
        def _sqlite_fk(dbapi_conn, _record) -> None:  # enforce FKs and ON DELETE CASCADE
            dbapi_conn.execute("PRAGMA foreign_keys=ON")
    return engine


def init_db(engine: sa.Engine) -> None:
    """Create missing tables, then drop and recreate every view in one
    transaction. Idempotent; safe on every startup (views hold no data).
    Raises on an unreachable database -- callers do this before measuring
    so a bad URL fails in milliseconds, not after a mutation run."""
    metadata.create_all(engine)
    with engine.begin() as conn:
        for name in reversed(VIEW_ORDER):
            conn.execute(sa.text(f"DROP VIEW IF EXISTS {name}"))
        for name in VIEW_ORDER:
            conn.execute(sa.text(f"CREATE VIEW {name} AS {VIEWS[name]}"))
