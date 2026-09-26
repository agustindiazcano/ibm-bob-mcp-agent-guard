"""The run record: one plain dict describing one measured run.

It's the single interchange format between measuring and storing: the
pipeline builds it, save_record() stores it locally, and `repoguard analyze
--push` sends the same dict to POST /api/runs, which validates and stores it
without recomputing anything. Pure Python on purpose -- `--push` must work
without the [db] extra.

Every number in it is copied from an engine result object; nothing here
computes, rounds or derives a metric.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from ..mutation import MUTATION_OPERATORS_HASH, OUTCOMES
from .context import RunContext

SCHEMA_VERSION = 1
MAX_MUTANTS = 50_000
MAX_TESTS = 50_000
MAX_FILES = 20_000
_TEST_OUTCOMES = ("passed", "failed", "error", "skipped")
_SOURCES = ("cli", "server", "ci", "mcp")


class RecordError(ValueError):
    """A run record that fails validation (bad shape, inconsistent counts,
    over a size cap)."""


def build_run_record(
    ctx: RunContext,
    *,
    project: str,
    source: str,
    started_at: datetime,
    finished_at: datetime,
    gate_threshold: float,
    coverage,
    mutation=None,
    risk: list | None = None,
    run_id: str | None = None,
) -> dict:
    """Build a run record from engine results (core.CoverageResult,
    mutation.MutationResult or None, list[core.RiskScore]). run_id is
    client-generated so a retried upload is idempotent."""
    record = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id or str(uuid.uuid4()),
        "project": project,
        "source": source,
        "commit_sha": ctx.commit_sha,
        "branch": ctx.branch,
        "dirty": ctx.dirty,
        "repository": ctx.repository,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "engine_version": ctx.engine_version,
        "operators_hash": MUTATION_OPERATORS_HASH,
        "python_version": ctx.python_version,
        "gate_threshold": gate_threshold,
        "coverage": {
            "percent": coverage.percent,
            "covered_lines": coverage.covered_lines,
            "total_lines": coverage.total_lines,
            "files": [
                {"file_path": path.replace("\\", "/"), "missing_lines": list(lines)}
                for path, lines in sorted(coverage.missing_lines.items())
            ],
        },
        "mutation": None,
        "risk": [
            {"file_path": r.file.replace("\\", "/"), "score": r.score, "rank": rank, "reasons": list(r.reasons)}
            for rank, r in enumerate(risk or [], start=1)
        ],
        "tests": [
            {"test_id": t.test_id, "outcome": t.outcome, "duration_s": t.duration_s}
            for t in getattr(coverage, "tests", [])
        ],
    }
    if mutation is not None:
        record["mutation"] = {
            "score": mutation.score,
            "killed": mutation.killed,
            "survived": mutation.survived,
            "total": mutation.total,
            "mutants": [
                {
                    "index": m.index,
                    "fingerprint": m.fingerprint,
                    "file_path": m.file,
                    "function_name": m.function,
                    "lineno": m.lineno,
                    "operator": m.operator,
                    "description": m.description,
                    "outcome": m.outcome,
                }
                for m in mutation.mutants
            ],
        }
    return record


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RecordError(message)


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_run_record(record: object) -> dict:
    """Check shape, internal consistency and size caps. Returns the record
    unchanged, or raises RecordError naming the first problem. Never fixes
    or recomputes anything."""
    _require(isinstance(record, dict), "record must be a JSON object")
    _require(record.get("schema_version") == SCHEMA_VERSION, f"schema_version must be {SCHEMA_VERSION}")
    try:
        uuid.UUID(str(record.get("run_id")))
    except ValueError:
        raise RecordError("run_id must be a UUID") from None
    _require(record.get("source") in _SOURCES, f"source must be one of {_SOURCES}")
    for key in ("started_at", "finished_at"):
        try:
            datetime.fromisoformat(str(record.get(key)))
        except ValueError:
            raise RecordError(f"{key} must be an ISO-8601 timestamp") from None
    _require(_number(record.get("gate_threshold")), "gate_threshold must be a number")

    cov = record.get("coverage")
    _require(isinstance(cov, dict), "coverage is required")
    _require(_number(cov.get("percent")) and 0 <= cov["percent"] <= 100, "coverage.percent must be 0-100")
    _require(isinstance(cov.get("covered_lines"), int) and isinstance(cov.get("total_lines"), int),
             "coverage line counts must be integers")
    _require(0 <= cov["covered_lines"] <= cov["total_lines"], "coverage.covered_lines must be <= total_lines")
    files = cov.get("files", [])
    _require(isinstance(files, list) and len(files) <= MAX_FILES, f"coverage.files must be a list of <= {MAX_FILES}")

    mutation = record.get("mutation")
    if mutation is not None:
        _require(isinstance(mutation, dict), "mutation must be an object or null")
        for key in ("killed", "survived", "total"):
            _require(isinstance(mutation.get(key), int) and mutation[key] >= 0, f"mutation.{key} must be an int >= 0")
        _require(mutation["killed"] + mutation["survived"] == mutation["total"], "mutation: killed + survived != total")
        _require(_number(mutation.get("score")), "mutation.score must be a number")
        mutants = mutation.get("mutants", [])
        _require(isinstance(mutants, list) and len(mutants) <= MAX_MUTANTS, f"mutation.mutants must be <= {MAX_MUTANTS}")
        if mutants:
            _require(len(mutants) == mutation["total"], "mutation: len(mutants) != total")
            _require(all(m.get("outcome") in OUTCOMES for m in mutants), f"mutant outcome must be one of {OUTCOMES}")
            survived = sum(1 for m in mutants if m.get("outcome") == "survived")
            _require(survived == mutation["survived"], "mutation: survived count doesn't match mutant outcomes")
            _require(len({m.get("index") for m in mutants}) == len(mutants), "mutant indexes must be unique")

    tests = record.get("tests", [])
    _require(isinstance(tests, list) and len(tests) <= MAX_TESTS, f"tests must be a list of <= {MAX_TESTS}")
    _require(all(t.get("outcome") in _TEST_OUTCOMES for t in tests), f"test outcome must be one of {_TEST_OUTCOMES}")
    _require(len({t.get("test_id") for t in tests}) == len(tests), "test_id values must be unique")

    risk = record.get("risk", [])
    _require(isinstance(risk, list) and len(risk) <= MAX_FILES, f"risk must be a list of <= {MAX_FILES}")
    return record
