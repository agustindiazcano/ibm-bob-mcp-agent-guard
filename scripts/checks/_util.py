"""Helpers shared by the standalone check scripts that scripts/verify.py
runs in a fresh interpreter (so sys.modules checks mean something)."""

from __future__ import annotations

import os
import shutil
import socket
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "demo-repo"
REFERENCE_TESTS = ROOT / "docs" / "expected-after-tests"


def temp_demo_copy(prefix: str = "repoguard_check_") -> Path:
    """A clean copy of demo-repo in a new temp dir (caller removes .parent)."""
    from repoguard_engine.core import COPY_IGNORE

    tmp = Path(tempfile.mkdtemp(prefix=prefix)) / "demo-repo"
    shutil.copytree(DEMO, tmp, ignore=COPY_IGNORE)
    return tmp


def add_reference_tests(repo: Path) -> None:
    for f in REFERENCE_TESTS.glob("test_*.py"):
        shutil.copy(f, repo / "tests" / f.name)


def sqlite_url(directory: Path) -> str:
    return f"sqlite:///{(directory / 'history.db').as_posix()}"


def test_database_urls(directory: Path) -> list[tuple[str, str]]:
    """(label, url) pairs to run a store check against: always a temp SQLite
    file, plus REPOGUARD_TEST_DATABASE_URL (e.g. CI's postgres:16 service)
    when set -- a SQLite PASS alone isn't proof Postgres works."""
    urls = [("sqlite", sqlite_url(directory))]
    extra = os.environ.get("REPOGUARD_TEST_DATABASE_URL")
    if extra:
        urls.append(("postgres" if extra.startswith("postgres") else "extra", extra))
    return urls


def reset_database(url: str) -> None:
    """Drop every view and table so a check starts from an empty schema.
    Only ever pointed at a throwaway test database."""
    import sqlalchemy as sa

    from repoguard_engine.store.db import get_engine
    from repoguard_engine.store.models import metadata
    from repoguard_engine.store.views import VIEW_ORDER

    engine = get_engine(url)
    with engine.begin() as conn:
        for name in reversed(VIEW_ORDER):
            conn.execute(sa.text(f"DROP VIEW IF EXISTS {name}"))
    metadata.drop_all(engine)


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
