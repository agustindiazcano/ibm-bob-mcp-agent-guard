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

# Which kinds of bugs the suite misses (latest run per project) -- portable:
# SUM(CASE ...) instead of COUNT(*) FILTER (...).
V_SURVIVAL_BY_OPERATOR = """
CREATE VIEW v_survival_by_operator AS
SELECT r.project_id, mu.operator,
       COUNT(*)                                              AS total,
       SUM(CASE WHEN mu.outcome != 'killed' THEN 1 ELSE 0 END) AS survived,
       ROUND(100.0 * SUM(CASE WHEN mu.outcome != 'killed' THEN 1 ELSE 0 END)
             / COUNT(*), 2)                                   AS survival_pct
FROM mutants mu
JOIN runs r ON r.id = mu.run_id
WHERE r.id = (SELECT id FROM runs r2
              WHERE r2.project_id = r.project_id AND r2.status = 'ok'
              ORDER BY started_at DESC LIMIT 1)
GROUP BY r.project_id, mu.operator
"""

# Persistent survivors: weak spots the suite has never caught -- portable:
# MAX(CASE ...) = 1 instead of HAVING BOOL_AND(NOT killed). Excludes runs
# from a dirty working tree so a fix-loop before/after pair sharing one
# commit sha doesn't get counted as "still surviving."
V_PERSISTENT_SURVIVORS = """
CREATE VIEW v_persistent_survivors AS
SELECT r.project_id, mu.fingerprint,
       MIN(mu.file_path)      AS file_path,
       MIN(mu.function_name)  AS function_name,
       MIN(mu.description)    AS description,
       COUNT(*)               AS runs_seen,
       MIN(r.started_at)      AS first_seen
FROM mutants mu
JOIN runs r ON r.id = mu.run_id
WHERE r.status = 'ok' AND NOT r.dirty
GROUP BY r.project_id, mu.fingerprint
HAVING MAX(CASE WHEN mu.outcome = 'killed' THEN 1 ELSE 0 END) = 0
"""

# Flaky tests: same commit, different outcomes -- portable: count of distinct
# outcomes instead of ARRAY_AGG. A dirty working tree (the fix loop, or
# copying reference tests in for verification) reuses the same commit sha
# with different tests -- restricted to non-dirty runs or every such session
# looks flaky.
V_FLAKY_TESTS = """
CREATE VIEW v_flaky_tests AS
SELECT r.project_id, r.commit_sha, t.test_id,
       COUNT(DISTINCT t.outcome) AS distinct_outcomes, COUNT(*) AS runs
FROM test_results t
JOIN runs r ON r.id = t.run_id
WHERE r.commit_sha IS NOT NULL AND NOT r.dirty
GROUP BY r.project_id, r.commit_sha, t.test_id
HAVING COUNT(DISTINCT t.outcome) > 1
"""

VIEWS: dict[str, str] = {
    "v_runs": V_RUNS,
    "v_run_trend": V_RUN_TREND,
    "v_survival_by_operator": V_SURVIVAL_BY_OPERATOR,
    "v_persistent_survivors": V_PERSISTENT_SURVIVORS,
    "v_flaky_tests": V_FLAKY_TESTS,
}
