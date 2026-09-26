"""Engine creation and schema setup. Every failure becomes a StoreError with
the password hidden, so callers can fail fast and print it safely."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from . import StoreError, normalize_url

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def get_engine(url: str) -> Engine:
    """A SQLAlchemy engine for *url* (cached per URL). Raises StoreError if the
    `[db]` extra is missing or the URL can't be parsed; doesn't connect yet."""
    try:
        import sqlalchemy  # noqa: F401
    except ImportError as exc:
        raise StoreError(
            f"REPOGUARD_DATABASE_URL is set but the [db] extra isn't installed ({exc}); "
            "run: pip install -e \".[db]\""
        ) from exc
    return _cached_engine(normalize_url(url))


@lru_cache(maxsize=8)
def _cached_engine(url: str) -> Engine:
    from sqlalchemy import create_engine, event
    from sqlalchemy.exc import ArgumentError, NoSuchModuleError

    try:
        engine = create_engine(url, pool_pre_ping=True)
    except (ArgumentError, NoSuchModuleError, ImportError, ValueError) as exc:
        raise StoreError(f"invalid database URL ({type(exc).__name__}: {exc})") from exc

    if engine.dialect.name == "sqlite":
        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_conn, _record) -> None:  # SQLite leaves FKs off by default
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def init_db(engine: Engine) -> None:
    """Create missing tables and (re)create every view, in one transaction.
    Idempotent. This is also the connectivity check: it's what makes a bad or
    unreachable database fail before a multi-minute measurement, not after."""
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError

    from .models import metadata
    from .views import VIEWS

    try:
        with engine.begin() as conn:
            metadata.create_all(conn)
            for name in VIEWS:
                conn.execute(text(f"DROP VIEW IF EXISTS {name}"))
            for ddl in VIEWS.values():
                conn.execute(text(ddl))
    except SQLAlchemyError as exc:
        raise StoreError(f"could not initialize the database at {describe(engine)}: {_short(exc)}") from exc


def describe(engine: Engine) -> str:
    """The engine URL with the password masked."""
    return engine.url.render_as_string(hide_password=True)


def _short(exc: Exception) -> str:
    # SQLAlchemy appends the SQL and a docs link; the first line is the cause.
    return str(getattr(exc, "orig", None) or exc).strip().splitlines()[0]
