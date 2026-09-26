"""Portable view DDL (SQLite and PostgreSQL): every derived value lives
here, computed on read from stored measurements -- never stored.

Portability rules (docs/DATA_PLATFORM.md §4.4): SUM(CASE ...) instead of
FILTER, MAX(CASE ...) instead of BOOL_AND, no ARRAY_AGG. Booleans are
compared with = TRUE/FALSE-free forms that work on both (SQLite stores
them as 0/1). ROUND() takes numeric on Postgres, so rates are computed
from a 100.0 literal (numeric), never from a double column.

"Survived" means outcome = 'survived'; timeouts and errors count as killed,
exactly as the engine scores them.
"""

from __future__ import annotations

VIEWS: dict[str, str] = {
    "v_runs": """
        SELECT r.id AS run_id, p.slug AS project, r.source, r.commit_sha, r.branch, r.dirty,
               r.started_at, r.finished_at, r.engine_version, r.operators_hash, r.gate_threshold,
               r.status, c.percent AS coverage_pct, m.score AS mutation_pct, m.killed, m.total
        FROM runs r
        JOIN projects p ON p.id = r.project_id
        LEFT JOIN coverage_results c ON c.run_id = r.id
        LEFT JOIN mutation_results m ON m.run_id = r.id
    """,
    "v_run_trend": """
        SELECT r.project_id, r.id AS run_id, r.commit_sha, r.started_at, r.operators_hash,
               c.percent AS coverage_pct,
               m.score AS mutation_pct,
               c.percent - m.score AS coverage_minus_mutation_pp,
               CASE WHEN c.percent >= r.gate_threshold THEN 1 ELSE 0 END AS passed_gate
        FROM runs r
        JOIN coverage_results c ON c.run_id = r.id
        LEFT JOIN mutation_results m ON m.run_id = r.id
        WHERE r.status = 'ok'
    """,
    "v_latest_mutation_run": """
        SELECT r.project_id, r.id AS run_id
        FROM runs r
        JOIN mutation_results m ON m.run_id = r.id
        WHERE r.status = 'ok' AND r.started_at = (
            SELECT MAX(r2.started_at) FROM runs r2
            JOIN mutation_results m2 ON m2.run_id = r2.id
            WHERE r2.project_id = r.project_id AND r2.status = 'ok'
        )
    """,
    "v_survival_by_operator": """
        SELECT lm.project_id, mu.operator,
               COUNT(*) AS total,
               SUM(CASE WHEN mu.outcome = 'survived' THEN 1 ELSE 0 END) AS survived,
               ROUND(100.0 * SUM(CASE WHEN mu.outcome = 'survived' THEN 1 ELSE 0 END) / COUNT(*), 2) AS survival_pct
        FROM mutants mu
        JOIN v_latest_mutation_run lm ON lm.run_id = mu.run_id
        GROUP BY lm.project_id, mu.operator
    """,
    "v_persistent_survivors": """
        SELECT r.project_id, mu.fingerprint,
               MIN(mu.file_path) AS file_path,
               MIN(mu.function_name) AS function_name,
               MIN(mu.lineno) AS lineno,
               MIN(mu.description) AS description,
               COUNT(*) AS runs_seen,
               MIN(r.started_at) AS first_seen
        FROM mutants mu
        JOIN runs r ON r.id = mu.run_id
        WHERE r.status = 'ok' AND NOT r.dirty
        GROUP BY r.project_id, mu.fingerprint
        HAVING MAX(CASE WHEN mu.outcome = 'survived' THEN 0 ELSE 1 END) = 0
    """,
    "v_flaky_tests": """
        SELECT r.project_id, r.commit_sha, t.test_id,
               COUNT(DISTINCT t.outcome) AS distinct_outcomes, COUNT(*) AS runs
        FROM test_results t
        JOIN runs r ON r.id = t.run_id
        WHERE r.commit_sha IS NOT NULL AND NOT r.dirty AND r.status = 'ok'
        GROUP BY r.project_id, r.commit_sha, t.test_id
        HAVING COUNT(DISTINCT t.outcome) > 1
    """,
    "v_fix_effect": """
        SELECT f.id, f.project_id, f.provider, f.model_id, f.created_at,
               f.before_run_id, f.after_run_id,
               mb.score AS before_pct, ma.score AS after_pct,
               ma.score - mb.score AS delta_pp,
               (SELECT COUNT(*) FROM test_results ta WHERE ta.run_id = f.after_run_id)
                 - (SELECT COUNT(*) FROM test_results tb WHERE tb.run_id = f.before_run_id) AS tests_added
        FROM fix_sessions f
        JOIN mutation_results mb ON mb.run_id = f.before_run_id
        JOIN mutation_results ma ON ma.run_id = f.after_run_id
    """,
}

# Creation order respects dependencies (v_survival_by_operator reads
# v_latest_mutation_run); drop order is the reverse.
VIEW_ORDER = list(VIEWS)
