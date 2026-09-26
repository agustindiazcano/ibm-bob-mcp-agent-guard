"""SQLAlchemy Core tables for measurement history (docs/DATA_PLATFORM.md §4.2).

Portable across SQLite and Postgres:
- ids are canonical UUID strings (String(36)), so every backend -- and every
  view -- returns the same representation;
- scores/percentages are Double, never Numeric, so a stored value equals the
  engine's float exactly (no rounding drift);
- list/dict columns are JSON (JSONB on Postgres).
Derived values (passed_gate, deltas, trends) are views, never columns.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON, Boolean, CheckConstraint, Column, DateTime, Double, ForeignKey, Index,
    Integer, MetaData, String, Table, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()

_Json = JSON().with_variant(JSONB(), "postgresql")


def _run_fk() -> Column:
    return Column("run_id", String(36), ForeignKey("runs.id", ondelete="CASCADE"), primary_key=True)


projects = Table(
    "projects", metadata,
    Column("id", String(36), primary_key=True),
    Column("slug", String(100), nullable=False),
    Column("repo_url", Text),
    Column("created_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("slug", name="uq_projects_slug"),
)

runs = Table(
    "runs", metadata,
    Column("id", String(36), primary_key=True),
    Column("project_id", String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
    # cli = written directly by a local engine process (CLI, MCP, library);
    # server = measured by the web service itself; ci = ingested via POST /api/runs
    Column("source", String(16), nullable=False),
    Column("commit_sha", String(64)),
    Column("branch", Text),
    Column("dirty", Boolean),  # NULL = unknown (not a git checkout / no git)
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("finished_at", DateTime(timezone=True), nullable=False),
    Column("engine_version", Text, nullable=False),
    Column("operators_hash", String(64), nullable=False),
    Column("python_version", Text, nullable=False),
    Column("gate_threshold", Double, nullable=False),
    Column("endpoints_measured", Boolean, nullable=False),
    Column("tests_measured", Boolean, nullable=False),
    Column("status", String(8), nullable=False),
    Column("error", Text),
    CheckConstraint("source IN ('cli', 'server', 'ci')", name="ck_runs_source"),
    CheckConstraint("status IN ('ok', 'error')", name="ck_runs_status"),
    Index("ix_runs_project_started", "project_id", "started_at"),
    Index("ix_runs_project_commit", "project_id", "commit_sha"),
)

coverage_results = Table(
    "coverage_results", metadata,
    _run_fk(),
    Column("percent", Double, nullable=False),
    Column("covered_lines", Integer, nullable=False),
    Column("total_lines", Integer, nullable=False),
)

# Only files with missing lines -- the engine keeps no row for a fully covered file.
file_coverage = Table(
    "file_coverage", metadata,
    _run_fk(),
    Column("file_path", Text, primary_key=True),
    Column("missing_count", Integer, nullable=False),
    Column("missing_lines", _Json, nullable=False),
)

# One row iff mutation was measured on that run.
mutation_results = Table(
    "mutation_results", metadata,
    _run_fk(),
    Column("score", Double, nullable=False),
    Column("killed", Integer, nullable=False),
    Column("survived", Integer, nullable=False),
    Column("total", Integer, nullable=False),
    CheckConstraint("killed + survived = total", name="ck_mutation_counts"),
)

# compute_risk only emits files that have missing lines: no row means "the
# engine emitted nothing", never an implicit zero score.
risk_scores = Table(
    "risk_scores", metadata,
    _run_fk(),
    Column("file_path", Text, primary_key=True),
    Column("score", Double, nullable=False),
    Column("rank", Integer, nullable=False),
    Column("reasons", _Json, nullable=False),
)

# Skeleton (decision #6): stored when runs.endpoints_measured is true, but no
# route or chart reads it yet -- see PENDING.md Phase 17.
endpoint_results = Table(
    "endpoint_results", metadata,
    _run_fk(),
    Column("ordinal", Integer, primary_key=True),
    Column("file_path", Text, nullable=False),
    Column("function_name", Text, nullable=False),
    Column("method", String(16), nullable=False),
    Column("path", Text, nullable=False),
    Column("has_test", Boolean, nullable=False),
)
