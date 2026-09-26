"""phase17 (aggregate data check): mutation runs persist per mutant, the
history views compute what the design says they compute, and a real
(scripted, credential-free) fix loop records its own fix session.
Runs against SQLite and, when set, REPOGUARD_TEST_DATABASE_URL."""

import json
import os
import shutil

import sqlalchemy as sa

from repoguard_engine.pipeline import run_pipeline
from repoguard_engine.store import models as m
from repoguard_engine.store.db import get_engine, init_db
from repoguard_engine.store.queries import fix_effect, operators, survivors, trend
from repoguard_engine.store.repository import save_fix_session
from repoguard_engine.testing import ScriptedProvider
from repoguard_engine.watson_agent import run_fix_loop

from _util import REFERENCE_TESTS, add_reference_tests, reset_database, temp_demo_copy, test_database_urls

base = temp_demo_copy()
try:
    for label, url in test_database_urls(base.parent):
        reset_database(url)
        engine = get_engine(url)
        init_db(engine)
        os.environ["REPOGUARD_DATABASE_URL"] = url
        os.environ["REPOGUARD_PROJECT"] = "demo"

        r1 = run_pipeline(base, include_mutation=True, mutation_workers=4)
        r2 = run_pipeline(base, include_mutation=True, mutation_workers=4)
        with engine.connect() as conn:
            mr = conn.execute(sa.select(m.mutation_results).where(m.mutation_results.c.run_id == r1.run_id)).one()
            assert (mr.killed, mr.survived, mr.total, mr.score) == (16, 63, 79, 20.25), mr
            rows = conn.execute(
                sa.select(m.mutants.c.mutant_index, m.mutants.c.fingerprint, m.mutants.c.outcome)
                .where(m.mutants.c.run_id == r1.run_id).order_by(m.mutants.c.mutant_index)
            ).all()
        on_disk = json.loads((base / "repoguard-out" / "mutants.json").read_text())["mutants"]
        assert [tuple(r) for r in rows] == [(x["index"], x["fingerprint"], x["outcome"]) for x in on_disk]
        surv = survivors(engine, "demo")
        assert len(surv) == 63 and all(s["runs_seen"] == 2 for s in surv), (len(surv), {s["runs_seen"] for s in surv})
        ops = operators(engine, "demo")
        assert sum(o["total"] for o in ops) == 79 and sum(o["survived"] for o in ops) == 63
        print(f"{label}: 2 mutation runs stored (16/79 each, 79 mutant rows = mutants.json); "
              f"63 persistent survivors seen in both; {len(ops)} operators sum to 79/63")

        after = temp_demo_copy()
        try:
            add_reference_tests(after)
            ra = run_pipeline(after, include_mutation=True, mutation_workers=4)
        finally:
            shutil.rmtree(after.parent, ignore_errors=True)
        assert (ra.mutation.killed, ra.mutation.total, ra.mutation.score) == (71, 79, 89.87)
        # Hand-made fix session over the reference "after" run: the effect
        # is whatever v_fix_effect derives from the two stored scores.
        save_fix_session(engine, project="demo", before_run_id=r1.run_id, after_run_id=ra.run_id,
                         provider="reference", model_id=None)
        ref = [f for f in fix_effect(engine, "demo") if f["provider"] == "reference"][0]
        assert round(ref["delta_pp"], 2) == 69.62 and ref["tests_added"] == 66, ref
        t = trend(engine, "demo")
        assert round(t[-1]["coverage_minus_mutation_pp"], 2) == 10.13, t[-1]
        print(f"{label}: after-reference stored 71/79 = 89.87; v_fix_effect delta {ref['delta_pp']:.2f} pp, "
              f"tests_added {ref['tests_added']}; coverage-minus-mutation gap 44.85 -> {t[-1]['coverage_minus_mutation_pp']:.2f} pp")

        fixed = temp_demo_copy()
        try:
            res = run_fix_loop(str(fixed), model=ScriptedProvider(REFERENCE_TESTS), mutation_workers=4)
        finally:
            shutil.rmtree(fixed.parent, ignore_errors=True)
        assert res.fix_session_id, "fix loop didn't record its session"
        real = [f for f in fix_effect(engine, "demo") if f["id"] == res.fix_session_id][0]
        assert real["provider"] == "scripted" and (real["before_pct"], real["after_pct"]) == (20.25, 86.08), real
        print(f"{label}: scripted fix loop recorded its own session: {real['before_pct']} -> {real['after_pct']} "
              f"({real['delta_pp']:.2f} pp, +{real['tests_added']} tests)")
    print("OK")
finally:
    os.environ.pop("REPOGUARD_DATABASE_URL", None)
    os.environ.pop("REPOGUARD_PROJECT", None)
    shutil.rmtree(base.parent, ignore_errors=True)
