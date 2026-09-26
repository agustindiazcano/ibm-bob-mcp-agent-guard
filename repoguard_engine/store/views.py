"""View DDL -- where every derived value lives (docs/DATA_PLATFORM.md §4.4).

Portable SQL only (runs unchanged on SQLite and Postgres): no FILTER,
BOOL_AND or ARRAY_AGG. init_db() drops and recreates these on every start,
since metadata.create_all() never creates views; views hold no data, so
that's safe.
"""

from __future__ import annotations

# Every run with its headline numbers. passed_gate is derived, never stored
# (decision #4); NULL when the run has no coverage (an error run).
V_RUNS = """
CREATE VIEW v_runs AS
SELECT r.id AS run_id, p.slug AS project, r.project_id, r.source,
       r.commit_sha, r.branch, r.dirty, r.started_at, r.finished_at,
       r.engine_version, r.operators_hash, r.python_version,
       r.gate_threshold, r.endpoints_measured, r.tests_measured,
       r.status, r.error,
       c.percent AS coverage_pct, c.covered_lines, c.total_lines,
       m.score AS mutation_pct, m.killed AS mutants_killed,
       m.survived AS mutants_survived, m.total AS mutants_total,
       CASE WHEN c.percent IS NULL THEN NULL
            WHEN c.percent >= r.gate_threshold THEN 1 ELSE 0 END AS passed_gate
FROM runs r
JOIN projects p ON p.id = r.project_id
LEFT JOIN coverage_results c ON c.run_id = r.id
LEFT JOIN mutation_results m ON m.run_id = r.id
"""

# Trend per commit: the "coverage lies" gap over time. Chart lines break
# where operators_hash changes (a different instrument, not a different suite).
V_RUN_TREND = """
CREATE VIEW v_run_trend AS
SELECT r.project_id, r.id AS run_id, r.commit_sha, r.started_at,
       r.operators_hash,
       c.percent                 AS coverage_pct,
       m.score                   AS mutation_pct,
       c.percent - m.score       AS coverage_minus_mutation_pp,
       CASE WHEN c.percent >= r.gate_threshold THEN 1 ELSE 0 END AS passed_gate
FROM runs r
JOIN coverage_results c ON c.run_id = r.id
LEFT JOIN mutation_results m ON m.run_id = r.id
WHERE r.status = 'ok'
"""

VIEWS: dict[str, str] = {
    "v_runs": V_RUNS,
    "v_run_trend": V_RUN_TREND,
}
