"""SQLAlchemy Core tables. One code path for SQLite (local, tests) and
PostgreSQL (Cloud SQL). Percent/score columns are Double, not Numeric, so
the engine's raw floats round-trip exactly (docs/DATA_PLATFORM.md §4.3).

Deliberately absent (derived in views.py instead): runs.passed_gate,
fix_sessions.tests_added. Deferred: endpoint_results (endpoints are opt-in
in `analyze`, so most rows would be an ambiguous "not measured").
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

metadata = sa.MetaData()

_JSON = sa.JSON().with_variant(JSONB(), "postgresql")
_ID = sa.String(36)  # UUID as text: identical on SQLite and Postgres


def _run_fk() -> sa.Column:
    return sa.Column("run_id", _ID, sa.ForeignKey("runs.id", ondelete="CASCADE"), primary_key=True)


projects = sa.Table(
    "projects", metadata,
    sa.Column("id", _ID, primary_key=True),
    sa.Column("slug", sa.String(200), nullable=False, unique=True),
    sa.Column("repo_url", sa.Text),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
)

api_tokens = sa.Table(
    "api_tokens", metadata,
    sa.Column("id", _ID, primary_key=True),
    sa.Column("project_id", _ID, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
    sa.Column("token_sha256", sa.String(64), nullable=False, unique=True),
    sa.Column("label", sa.Text),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("revoked_at", sa.DateTime(timezone=True)),
)

runs = sa.Table(
    "runs", metadata,
    sa.Column("id", _ID, primary_key=True),
    sa.Column("project_id", _ID, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
    sa.Column("source", sa.String(16), nullable=False),
    sa.Column("commit_sha", sa.String(64)),
    sa.Column("branch", sa.Text),
    sa.Column("dirty", sa.Boolean, nullable=False, default=False),
    sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("engine_version", sa.String(64), nullable=False),
    sa.Column("operators_hash", sa.String(64), nullable=False),
    sa.Column("python_version", sa.String(32), nullable=False),
    sa.Column("gate_threshold", sa.Double, nullable=False),
    sa.Column("tests_measured", sa.Boolean, nullable=False),
    sa.Column("status", sa.String(8), nullable=False, default="ok"),
    sa.Column("error", sa.Text),
    sa.CheckConstraint("status IN ('ok', 'error')", name="ck_runs_status"),
    sa.Index("ix_runs_project_started", "project_id", "started_at"),
    sa.Index("ix_runs_project_commit", "project_id", "commit_sha"),
)

coverage_results = sa.Table(
    "coverage_results", metadata,
    _run_fk(),
    sa.Column("percent", sa.Double, nullable=False),
    sa.Column("covered_lines", sa.Integer, nullable=False),
    sa.Column("total_lines", sa.Integer, nullable=False),
)

file_coverage = sa.Table(
    "file_coverage", metadata,
    _run_fk(),
    sa.Column("file_path", sa.String(1024), primary_key=True),
    sa.Column("missing_count", sa.Integer, nullable=False),
    sa.Column("missing_lines", _JSON, nullable=False),
)

mutation_results = sa.Table(
    "mutation_results", metadata,
    _run_fk(),
    sa.Column("score", sa.Double, nullable=False),
    sa.Column("killed", sa.Integer, nullable=False),
    sa.Column("survived", sa.Integer, nullable=False),
    sa.Column("total", sa.Integer, nullable=False),
    sa.CheckConstraint("killed + survived = total", name="ck_mutation_counts"),
)

mutants = sa.Table(
    "mutants", metadata,
    _run_fk(),
    sa.Column("mutant_index", sa.Integer, primary_key=True),
    sa.Column("fingerprint", sa.String(40), nullable=False),
    sa.Column("file_path", sa.String(1024), nullable=False),
    sa.Column("function_name", sa.Text, nullable=False),
    sa.Column("lineno", sa.Integer, nullable=False),
    sa.Column("operator", sa.String(32), nullable=False),
    sa.Column("description", sa.Text, nullable=False),
    sa.Column("outcome", sa.String(8), nullable=False),
    sa.CheckConstraint("outcome IN ('killed', 'survived', 'timeout', 'error')", name="ck_mutants_outcome"),
    sa.Index("ix_mutants_fingerprint", "fingerprint"),
)

risk_scores = sa.Table(
    "risk_scores", metadata,
    _run_fk(),
    sa.Column("file_path", sa.String(1024), primary_key=True),
    sa.Column("score", sa.Double, nullable=False),
    sa.Column("rank", sa.Integer, nullable=False),
    sa.Column("reasons", _JSON, nullable=False),
)

test_results = sa.Table(
    "test_results", metadata,
    _run_fk(),
    sa.Column("test_id", sa.String(1024), primary_key=True),
    sa.Column("outcome", sa.String(8), nullable=False),
    sa.Column("duration_s", sa.Double, nullable=False),
    sa.CheckConstraint("outcome IN ('passed', 'failed', 'error', 'skipped')", name="ck_tests_outcome"),
)

fix_sessions = sa.Table(
    "fix_sessions", metadata,
    sa.Column("id", _ID, primary_key=True),
    sa.Column("project_id", _ID, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
    sa.Column("before_run_id", _ID, sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False),
    sa.Column("after_run_id", _ID, sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False),
    sa.Column("provider", sa.String(32), nullable=False),
    sa.Column("model_id", sa.Text),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
)
