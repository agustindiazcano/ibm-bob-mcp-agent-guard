"""phase17-store: the store stays inert without a database URL, and a real
demo-repo measurement round-trips through it exactly (SQLite, plus
REPOGUARD_TEST_DATABASE_URL when set)."""

import os
import shutil
import sys

os.environ.pop("REPOGUARD_DATABASE_URL", None)

import repoguard_engine  # noqa: E402
from repoguard_engine.pipeline import run_pipeline  # noqa: E402

from _util import reset_database, temp_demo_copy, test_database_urls  # noqa: E402

repo = temp_demo_copy()
try:
    result = run_pipeline(repo, build_record=True)
    assert result.run_id is None, "persisted with no REPOGUARD_DATABASE_URL"
    assert "sqlalchemy" not in sys.modules, "SQLAlchemy imported with persistence off"
    print(f"persistence off: no DB write, SQLAlchemy not imported; coverage {result.coverage.percent:.1f}%")

    import sqlalchemy as sa

    from repoguard_engine.store import models as m
    from repoguard_engine.store.db import get_engine, init_db
    from repoguard_engine.store.repository import save_record

    record = result.record
    for label, url in test_database_urls(repo.parent):
        reset_database(url)
        engine = get_engine(url)
        init_db(engine)
        init_db(engine)  # idempotent: views dropped and recreated
        run_id, created = save_record(engine, record)
        assert created and run_id == record["run_id"]
        again, created = save_record(engine, record)
        assert again == run_id and not created, "same run_id stored twice"
        with engine.connect() as conn:
            cov = conn.execute(sa.select(m.coverage_results).where(m.coverage_results.c.run_id == run_id)).one()
            assert cov.percent == result.coverage.percent, (cov.percent, result.coverage.percent)
            assert (cov.covered_lines, cov.total_lines) == (result.coverage.covered_lines, result.coverage.total_lines)
            stored_missing = {
                r.file_path: r.missing_lines
                for r in conn.execute(sa.select(m.file_coverage).where(m.file_coverage.c.run_id == run_id))
            }
            engine_missing = {k.replace("\\", "/"): v for k, v in result.coverage.missing_lines.items()}
            assert stored_missing == engine_missing, "missing_lines differ after the round trip"
            stored_risk = {
                r.file_path: (r.score, r.rank)
                for r in conn.execute(sa.select(m.risk_scores).where(m.risk_scores.c.run_id == run_id))
            }
            assert stored_risk == {r.file.replace("\\", "/"): (r.score, i) for i, r in enumerate(result.risk, 1)}
            tests = conn.execute(sa.select(sa.func.count()).select_from(m.test_results).where(m.test_results.c.run_id == run_id)).scalar()
            assert tests == 5, tests
            view = conn.execute(sa.text("SELECT coverage_pct, passed_gate FROM v_run_trend WHERE run_id = :r"), {"r": run_id}).one()
            assert view.coverage_pct == result.coverage.percent and view.passed_gate == 0
        print(f"{label}: exact round trip (coverage {cov.percent!r}, {len(stored_missing)} files, "
              f"{len(stored_risk)} risk rows, {tests} tests), idempotent save, init_db twice, view reads it")
    print("OK")
finally:
    shutil.rmtree(repo.parent, ignore_errors=True)
