"""phase17-pipeline: persisting can't change a measured number, a stored
run matches the returned result exactly, and a bad database URL fails
before any measurement runs."""

import os
import shutil
import time

import sqlalchemy as sa

from repoguard_engine.pipeline import run_pipeline
from repoguard_engine.store import models as m
from repoguard_engine.store.db import get_engine

from _util import sqlite_url, temp_demo_copy

a = temp_demo_copy()
b = temp_demo_copy()
try:
    os.environ.pop("REPOGUARD_DATABASE_URL", None)
    ra = run_pipeline(a)
    url = sqlite_url(b.parent)
    os.environ["REPOGUARD_DATABASE_URL"] = url
    rb = run_pipeline(b)
    for name in ("coverage.json", "gaps.json", "risk.json"):
        path_a, path_b = a / "repoguard-out" / name, b / "repoguard-out" / name
        if path_a.exists() or path_b.exists():
            assert path_a.read_bytes() == path_b.read_bytes(), f"{name} differs with persistence on"
    assert ra.dashboard == rb.dashboard, "dashboard differs with persistence on"
    assert ra.run_id is None and not list(a.parent.glob("*.db")), "run A wrote a database"
    print("outputs byte-identical with persistence off vs on; run A wrote no database")

    engine = get_engine(url)
    with engine.connect() as conn:
        runs = conn.execute(sa.select(m.runs)).all()
        assert len(runs) == 1 and runs[0].id == rb.run_id, runs
        cov = conn.execute(sa.select(m.coverage_results)).one()
        assert cov.percent == rb.coverage.percent
        assert runs[0].source == "cli" and runs[0].gate_threshold == 80.0
    print(f"stored 1 run {rb.run_id} matching the returned result exactly")

    c = temp_demo_copy()
    try:
        os.environ["REPOGUARD_DATABASE_URL"] = "postgresql+psycopg://nobody@127.0.0.1:1/none?connect_timeout=2"
        t = time.perf_counter()
        try:
            run_pipeline(c)
            raise AssertionError("expected a connection error for an unreachable database")
        except sa.exc.OperationalError:
            pass
        elapsed = time.perf_counter() - t
        assert elapsed < 5, elapsed
        assert not (c / "repoguard-out").exists(), "measured before checking the database"
        print(f"unreachable DB fails in {elapsed:.2f} s, before pytest runs (no repoguard-out/)")
    finally:
        shutil.rmtree(c.parent, ignore_errors=True)
    print("OK")
finally:
    os.environ.pop("REPOGUARD_DATABASE_URL", None)
    shutil.rmtree(a.parent, ignore_errors=True)
    shutil.rmtree(b.parent, ignore_errors=True)
