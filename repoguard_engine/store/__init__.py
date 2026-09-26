"""Run history: every measured run, stored per project and commit.

The engine measures; this package only stores what it measured and reads it
back. Derived values (passed_gate, deltas, trends, survival rates) are SQL
views (views.py), never stored columns. Persistence is off unless
REPOGUARD_DATABASE_URL is set, and it can't change a measured number.

This module deliberately imports nothing from SQLAlchemy: `import
repoguard_engine` must not pull in the optional [db] extra. Only db.py,
models.py, repository.py and queries.py need it, and callers import those
lazily, on the code path that actually persists.

See docs/DATA_PLATFORM.md (schema, views, API) for the design.
"""

from __future__ import annotations

import os

DATABASE_URL_ENV = "REPOGUARD_DATABASE_URL"


class StoreNotConfigured(RuntimeError):
    """Persistence was requested but REPOGUARD_DATABASE_URL isn't set."""


def database_url() -> str | None:
    """The configured database URL, read at call time (never cached)."""
    return os.environ.get(DATABASE_URL_ENV) or None


def is_enabled() -> bool:
    return database_url() is not None
