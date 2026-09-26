"""
Phase 17 checks for scripts/verify.py (measurement history store).

    phase17-store     — store stays inert without REPOGUARD_DATABASE_URL (no sqlalchemy import);
                        a real demo-repo result + a real small mutation run round-trip through
                        SQLite (and REPOGUARD_TEST_DATABASE_URL, e.g. Postgres, when set) with
                        exact equality; init_db is idempotent; views return the rows; record
                        validation, git context and slug rules
    phase17-pipeline  — persisting can't change a measurement: demo-repo with mutation, stored vs.
                        not stored, byte-identical repoguard-out/*.json; stored 16/79 = 20.25;
                        bad URL / missing [db] fail before measuring; CLI output; web and the
                        MCP summary tool never write

Each check runs its script in a fresh interpreter (sys.executable), same as verify.py.
"""

from __future__ import annotations

import subprocess
import sys


def _run_script(script: str, timeout: int) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout + proc.stderr


_COMMON = r"""
import os, shutil, sys, tempfile
from pathlib import Path
for var in ('REPOGUARD_DATABASE_URL', 'REPOGUARD_PROJECT', 'GITHUB_REPOSITORY', 'GITHUB_SHA',
            'GITHUB_REF_NAME', 'GITHUB_HEAD_REF'):
    os.environ.pop(var, None)

def copy_demo(dest):
    return Path(shutil.copytree('demo-repo', Path(dest) / 'demo-repo',
                ignore=shutil.ignore_patterns('repoguard-out', '__pycache__', '.pytest_cache')))
"""

_STORE = _COMMON + r"""
import subprocess
from datetime import datetime, timezone
import repoguard_engine
from repoguard_engine.pipeline import run_pipeline

tmp = Path(tempfile.mkdtemp(prefix='verify17-'))
try:
    # 1. Persistence off: the engine never imports SQLAlchemy
    demo = run_pipeline(copy_demo(tmp))
    assert demo.run_id is None, 'a run was stored with REPOGUARD_DATABASE_URL unset'
    assert 'sqlalchemy' not in sys.modules, 'sqlalchemy imported with persistence off'
    print('  inert without REPOGUARD_DATABASE_URL: no run stored, sqlalchemy not imported')

    # A real mutation run on a tiny fixture, to exercise mutation_results with real numbers
    small = tmp / 'small'; (small / 'tests').mkdir(parents=True)
    (small / 'calc.py').write_text('def add(a, b):\n    return a + b\n\ndef double(x):\n    return x * 2\n')
    (small / 'tests' / 'test_calc.py').write_text(
        'from calc import add, double\n\ndef test_add():\n    assert add(2, 3) == 5\n\n'
        'def test_double():\n    assert double(0) == 0\n')
    (small / 'pytest.ini').write_text('[pytest]\npythonpath = .\n')
    mut = run_pipeline(small, include_mutation=True, include_endpoints=False)
    assert mut.mutation.total > 0 and mut.mutation.survived > 0, f'fixture should leave survivors: {mut.mutation}'

    from repoguard_engine.core import MUTATION_OPERATORS_HASH
    from repoguard_engine.store import StoreError
    from repoguard_engine.store.context import collect_context, resolve_project_slug
    from repoguard_engine.store.db import get_engine, init_db
    from repoguard_engine.store.record import build_run_record, new_run_id, validate_run_record
    from repoguard_engine.store.repository import save_record
    from repoguard_engine.store.models import (coverage_results, endpoint_results, file_coverage,
                                               mutation_results, risk_scores, runs)
    from sqlalchemy import select, text

    def record_for(result, endpoints):
        now = datetime.now(timezone.utc)
        return build_run_record(collect_context(result.repo_path, 'verify-store'), run_id=new_run_id(),
                                started_at=now, finished_at=now, gate_threshold=result.gate_threshold,
                                coverage=result.coverage, mutation=result.mutation, risk=result.risk,
                                endpoints=endpoints)

    rec_demo = record_for(demo, demo.endpoints)
    rec_mut = record_for(mut, None)
    assert len(rec_demo['endpoints']) == len(demo.endpoints) > 0

    # 2-3. Round trip on every configured backend
    urls = [('sqlite', f'sqlite:///{tmp / "store.db"}')]
    if os.environ.get('REPOGUARD_TEST_DATABASE_URL'):
        urls.append(('test-db', os.environ['REPOGUARD_TEST_DATABASE_URL']))
    for label, url in urls:
        engine = get_engine(url)
        init_db(engine); init_db(engine)
        id_demo = save_record(engine, rec_demo, project='verify-store', source='cli')
        id_mut = save_record(engine, rec_mut, project='verify-store', source='cli')
        with engine.connect() as c:
            row = c.execute(select(coverage_results).where(coverage_results.c.run_id == id_demo)).one()
            assert row.percent == demo.coverage.percent, f'{label}: coverage {row.percent!r} != {demo.coverage.percent!r}'
            assert (row.covered_lines, row.total_lines) == (demo.coverage.covered_lines, demo.coverage.total_lines)
            stored_missing = dict(c.execute(select(file_coverage.c.file_path, file_coverage.c.missing_lines)
                                            .where(file_coverage.c.run_id == id_demo)).all())
            assert stored_missing == {Path(f).as_posix(): l for f, l in demo.coverage.missing_lines.items()}, f'{label}: missing_lines differ'
            stored_risk = c.execute(select(risk_scores.c.file_path, risk_scores.c.score, risk_scores.c.rank)
                                    .where(risk_scores.c.run_id == id_demo).order_by(risk_scores.c.rank)).all()
            assert [tuple(r) for r in stored_risk] == [(Path(r.file).as_posix(), r.score, i) for i, r in enumerate(demo.risk, 1)], f'{label}: risk differs'
            eps = c.execute(select(endpoint_results).where(endpoint_results.c.run_id == id_demo)
                            .order_by(endpoint_results.c.ordinal)).all()
            assert [(e.method, e.path, e.function_name, e.has_test) for e in eps] == \
                   [(e.method, e.path, e.function, e.has_test) for e in demo.endpoints], f'{label}: endpoints differ'
            assert c.execute(select(mutation_results).where(mutation_results.c.run_id == id_demo)).first() is None
            m = c.execute(select(mutation_results).where(mutation_results.c.run_id == id_mut)).one()
            assert (m.score, m.killed, m.survived, m.total) == (mut.mutation.score, mut.mutation.killed, mut.mutation.survived, mut.mutation.total), f'{label}: mutation differs'
            r = c.execute(select(runs).where(runs.c.id == id_demo)).one()
            assert r.endpoints_measured is True and r.tests_measured is False and r.source == 'cli'
            assert r.operators_hash == MUTATION_OPERATORS_HASH and r.status == 'ok'
            assert c.execute(select(runs.c.endpoints_measured).where(runs.c.id == id_mut)).scalar_one() is False
        init_db(engine)  # views are dropped and recreated; the data must survive
        with engine.connect() as c:
            v = c.execute(text('SELECT coverage_pct, passed_gate FROM v_runs WHERE run_id = :i'), {'i': id_demo}).one()
            assert v.coverage_pct == demo.coverage.percent
            assert v.passed_gate == int(demo.coverage.percent >= demo.gate_threshold)
            t = c.execute(text('SELECT mutation_pct, coverage_minus_mutation_pp FROM v_run_trend WHERE run_id = :i'), {'i': id_mut}).one()
            assert t.mutation_pct == mut.mutation.score
            assert abs(t.coverage_minus_mutation_pp - (mut.coverage.percent - mut.mutation.score)) < 1e-9
        print(f'  {label} ({engine.dialect.name}): exact round trip (coverage {demo.coverage.percent!r}, '
              f'{len(stored_risk)} risk rows, {len(eps)} endpoints, mutation {m.killed}/{m.total}), '
              f'init_db x3 idempotent, views OK')

    # 4. Record validation rejects inconsistent bodies
    bad = [dict(rec_mut, mutation={**rec_mut['mutation'], 'killed': rec_mut['mutation']['killed'] + 1}),
           dict(rec_demo, run_id='not-a-uuid'), dict(rec_demo, extra=1),
           dict(rec_demo, started_at='2026-01-01T00:00:00'),
           dict(rec_demo, coverage={**rec_demo['coverage'], 'percent': True})]
    for b in bad:
        try:
            validate_run_record(b); raise AssertionError(f'accepted an invalid record: {sorted(set(b) ^ set(rec_demo))}')
        except ValueError:
            pass
    print(f'  validate_run_record rejects {len(bad)} malformed records')

    # 5. Git context and dirty detection on a throwaway repo
    g = tmp / 'gitrepo'; g.mkdir()
    git = lambda *a: subprocess.run(['git', '-c', 'user.email=v@x', '-c', 'user.name=v', *a], cwd=g,
                                    check=True, capture_output=True, timeout=30)
    git('init', '-q'); (g / 'mod.py').write_text('x = 1\n'); git('add', '.'); git('commit', '-qm', 'init')
    ctx = collect_context(g)
    assert ctx.dirty is False and len(ctx.commit_sha) == 40, ctx
    for artifact in ('repoguard-out/coverage.json', '__pycache__/mod.cpython-311.pyc', '.pytest_cache/v/x', '.coverage'):
        (g / artifact).parent.mkdir(parents=True, exist_ok=True); (g / artifact).write_text('{}')
    assert collect_context(g).dirty is False, 'tool artifacts counted as dirty'
    (g / 'test_new.py').write_text('def test_x(): pass\n')
    assert collect_context(g).dirty is True, 'an untracked test file must count as dirty'
    assert collect_context(tmp / 'small').dirty is None, 'outside git, dirty must be unknown (None)'
    print('  git context: sha + clean tree, tool artifacts ignored, new test file -> dirty, no git -> None')

    # 6. Slug precedence (decision #3)
    assert resolve_project_slug(g, 'explicit') == 'explicit'
    os.environ['REPOGUARD_PROJECT'] = 'from-env'; assert resolve_project_slug(g) == 'from-env'; del os.environ['REPOGUARD_PROJECT']
    os.environ['GITHUB_REPOSITORY'] = 'Owner/My.Repo'; assert resolve_project_slug(g) == 'owner-my.repo'; del os.environ['GITHUB_REPOSITORY']
    assert resolve_project_slug(g) == 'gitrepo'
    try:
        resolve_project_slug(g, 'Bad Slug'); raise AssertionError('accepted an invalid explicit slug')
    except StoreError:
        pass
    print('  project slug: --project > REPOGUARD_PROJECT > GITHUB_REPOSITORY > dir name; invalid explicit slug rejected')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print('OK')
"""

_PIPELINE = _COMMON + r"""
import json, subprocess, time
from fastapi.testclient import TestClient

tmp = Path(tempfile.mkdtemp(prefix='verify17p-'))
db_path = tmp / 'history.db'
url = f'sqlite:///{db_path}'
try:
    from repoguard_engine.pipeline import run_pipeline
    from repoguard_engine.store import StoreError

    # Run A: persistence off
    a_repo = copy_demo(tmp / 'a')
    a = run_pipeline(a_repo, include_mutation=True)
    assert a.run_id is None and not db_path.exists(), 'run A wrote to the database'

    # Run B: persistence on
    os.environ['REPOGUARD_DATABASE_URL'] = url
    b_repo = copy_demo(tmp / 'b')
    b = run_pipeline(b_repo, include_mutation=True)
    assert b.run_id and b.project == 'demo-repo', (b.run_id, b.project)
    for name in ('coverage', 'risk', 'mutation'):
        fa, fb = a_repo / 'repoguard-out' / f'{name}.json', b_repo / 'repoguard-out' / f'{name}.json'
        assert fa.read_bytes() == fb.read_bytes(), f'{name}.json differs when the run is stored'
    assert (b.mutation.killed, b.mutation.total, b.mutation.score) == (16, 79, 20.25), \
        f'mutation {b.mutation.killed}/{b.mutation.total} = {b.mutation.score}; AGENTS.md Section 7 baseline is 16/79 = 20.25'
    print(f'  stored vs. not stored: coverage/risk/mutation.json byte-identical; mutation {b.mutation.killed}/{b.mutation.total} = {b.mutation.score}%')

    from sqlalchemy import text
    from repoguard_engine.store.db import get_engine
    engine = get_engine(url)
    def run_count():
        with engine.connect() as c:
            return c.execute(text('SELECT COUNT(*) FROM runs')).scalar_one()
    with engine.connect() as c:
        v = c.execute(text('SELECT * FROM v_runs')).one()
    assert run_count() == 1 and v.run_id == b.run_id
    assert (v.coverage_pct, v.mutation_pct, v.mutants_killed, v.mutants_total) == \
           (b.coverage.percent, b.mutation.score, b.mutation.killed, b.mutation.total)
    assert v.endpoints_measured == 1 and v.project == 'demo-repo'
    print(f'  database: 1 run, v_runs equals the PipelineResult exactly (coverage {v.coverage_pct!r})')

    # Fail fast, before measuring
    for label, env_url, extra in (('unreachable DB', 'postgresql://nobody:secret@127.0.0.1:1/none', ''),
                                  ('missing [db] extra', url, "sys.modules['sqlalchemy'] = None; ")):
        c_repo = copy_demo(tmp / ('c-' + label.split()[0]))
        script = (f"import sys; {extra}from repoguard_engine.pipeline import run_pipeline\n"
                  f"from repoguard_engine.store import StoreError\n"
                  f"try:\n    run_pipeline({str(c_repo)!r}, include_mutation=True)\n"
                  f"except StoreError as e:\n    print('StoreError:', e); raise SystemExit(0)\n"
                  f"raise SystemExit('no StoreError')")
        t0 = time.monotonic()
        p = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True, timeout=60,
                           env={**os.environ, 'REPOGUARD_DATABASE_URL': env_url})
        elapsed = time.monotonic() - t0
        assert p.returncode == 0, p.stdout + p.stderr
        assert elapsed < 5, f'{label}: took {elapsed:.1f}s -- did it measure first?'
        assert not (c_repo / 'repoguard-out').exists(), f'{label}: measured before failing'
        assert 'secret' not in p.stdout, 'password leaked into the error message'
        print(f'  {label}: StoreError in {elapsed:.2f}s, nothing measured -- {p.stdout.strip().splitlines()[0][:90]}')

    # CLI: --project, run id on stderr, stdout is pure JSON
    cli = [sys.executable, '-c', 'from repoguard_engine.cli import main; main()']  # this interpreter, not PATH
    p = subprocess.run([*cli, 'analyze', str(b_repo), '--project', 'verify-cli', '--json-output'],
                       capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stderr
    json.loads(p.stdout)
    assert 'Stored run' in p.stderr and '(project verify-cli)' in p.stderr and 'Stored run' not in p.stdout
    p = subprocess.run([*cli, 'analyze', str(b_repo)], capture_output=True, text=True, timeout=60,
                       env={**os.environ, 'REPOGUARD_DATABASE_URL': 'postgresql://nobody:x@127.0.0.1:1/none'})
    assert p.returncode == 1 and 'Storage failed' in p.stderr and 'Traceback' not in p.stderr, p.stderr
    no_db = [sys.executable, '-c', "import sys; sys.modules['sqlalchemy'] = None; from repoguard_engine.cli import main; main()"]
    p = subprocess.run([*no_db, 'analyze', str(b_repo)], capture_output=True, text=True, timeout=60)
    # Rich reads '[db]' as markup unless escaped -- the install hint must survive printing
    assert p.returncode == 1 and 'pip install -e ".[db]"' in ' '.join(p.stderr.split()), p.stderr
    assert run_count() == 2
    print('  CLI: --project stored, run id on stderr, stdout pure JSON; bad DB / no [db] -> exit 1, real install hint, no traceback')

    # Web /api/analyze never writes (decision #5); MCP: full pipeline stores, summary doesn't
    from repoguard_engine.web.server import app
    res = TestClient(app).get('/api/analyze', params={'repo_path': str(b_repo)})
    assert res.status_code == 200 and 'run_id' not in res.json() and run_count() == 2, 'web /api/analyze stored a run'
    import repoguard_engine.mcp_server as m
    out = m.tool_full_pipeline(str(b_repo))
    assert out.get('run_id') and run_count() == 3, out
    m.tool_generate_summary(str(b_repo))
    assert run_count() == 3, 'tool_generate_summary stored a run'
    print('  web /api/analyze: not stored; MCP tool_full_pipeline: stored (run_id in compact); tool_generate_summary: not stored')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print('OK')
"""


def _check(title: str, script: str, timeout: int) -> bool:
    print(f"=== {title} ===")
    rc, out = _run_script(script, timeout)
    print(out.rstrip())
    ok = rc == 0 and out.rstrip().endswith("OK")
    print(f"  -> {'PASS' if ok else 'FAIL'}")
    return ok


def check_phase17_store() -> bool:
    return _check("Phase 17 A1.1: store round trip (SQLite + REPOGUARD_TEST_DATABASE_URL)", _STORE, timeout=300)


def check_phase17_pipeline() -> bool:
    return _check("Phase 17 A1.2: pipeline persistence can't change a measurement", _PIPELINE, timeout=900)
