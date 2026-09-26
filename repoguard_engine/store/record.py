"""The run record: one plain dict per measured run, the single interchange
format between the pipeline, the local store and (Phase 17 A3) the
POST /api/runs ingest path.

No SQLAlchemy import, so a record can be built and validated without the
`[db]` extra. Numbers are copied verbatim from the engine's dataclasses --
nothing here computes, rounds or fills in a metric.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..api_check import EndpointInfo
    from ..core import CoverageResult, MutationResult, RiskScore
    from .context import RunContext

SCHEMA_VERSION = 1
MAX_ITEMS = 50_000  # per list/dict in a record; bounds what an ingest body can make the server store

_CONTEXT_KEYS = (
    "repo_url", "commit_sha", "branch", "dirty",
    "engine_version", "operators_hash", "python_version",
)


def build_run_record(
    ctx: RunContext,
    *,
    run_id: str,
    started_at: datetime,
    finished_at: datetime,
    gate_threshold: float,
    coverage: CoverageResult,
    mutation: MutationResult | None,
    risk: list[RiskScore],
    endpoints: list[EndpointInfo] | None,
) -> dict[str, Any]:
    """Assemble a validated run record from engine results. `endpoints=None`
    means endpoints were not measured (distinct from an empty list)."""
    context = {key: getattr(ctx, key) for key in _CONTEXT_KEYS}
    record = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "status": "ok",
        "error": None,
        "gate_threshold": gate_threshold,
        "context": context,
        "coverage": {
            "percent": coverage.percent,
            "covered_lines": coverage.covered_lines,
            "total_lines": coverage.total_lines,
            "missing_lines": {_posix(f): list(lines) for f, lines in coverage.missing_lines.items()},
        },
        "mutation": (
            {"score": mutation.score, "killed": mutation.killed,
             "survived": mutation.survived, "total": mutation.total}
            if mutation is not None else None
        ),
        # rank is the engine's own sort order (compute_risk sorts by score), stored as-is
        "risk": [
            {"file": _posix(r.file), "score": r.score, "rank": i, "reasons": list(r.reasons)}
            for i, r in enumerate(risk, start=1)
        ],
        "endpoints": (
            [{**asdict(e), "file": _posix(e.file)} for e in endpoints]
            if endpoints is not None else None
        ),
    }
    validate_run_record(record)
    return record


def validate_run_record(record: Any) -> None:
    """Raise ValueError unless *record* is a well-formed schema-1 run record.
    Checks shape and internal consistency only; it never recomputes a metric."""
    _require(isinstance(record, dict), "record must be an object")
    _require(record.get("schema_version") == SCHEMA_VERSION, f"schema_version must be {SCHEMA_VERSION}")
    known = {"schema_version", "run_id", "started_at", "finished_at", "status", "error",
             "gate_threshold", "context", "coverage", "mutation", "risk", "endpoints"}
    unknown = set(record) - known
    _require(not unknown, f"unknown fields: {sorted(unknown)}")

    run_id = record.get("run_id")
    _require(isinstance(run_id, str) and _is_canonical_uuid(run_id), "run_id must be a lowercase canonical UUID string")
    started, finished = _timestamp(record, "started_at"), _timestamp(record, "finished_at")
    _require(finished >= started, "finished_at is before started_at")
    _require(record.get("status") in ("ok", "error"), "status must be 'ok' or 'error'")
    _require(record.get("error") is None or isinstance(record["error"], str), "error must be a string or null")
    _require(_is_number(record.get("gate_threshold")), "gate_threshold must be a number")

    ctx = record.get("context")
    _require(isinstance(ctx, dict) and set(ctx) == set(_CONTEXT_KEYS), f"context must have exactly {list(_CONTEXT_KEYS)}")
    for key in ("engine_version", "operators_hash", "python_version"):
        _require(isinstance(ctx[key], str) and ctx[key], f"context.{key} must be a non-empty string")
    for key in ("repo_url", "commit_sha", "branch"):
        _require(ctx[key] is None or isinstance(ctx[key], str), f"context.{key} must be a string or null")
    _require(ctx["dirty"] is None or isinstance(ctx["dirty"], bool), "context.dirty must be a boolean or null")

    cov = record.get("coverage")
    if record["status"] == "error":
        _require(cov is None, "an error run carries no coverage")
    else:
        _require(isinstance(cov, dict), "coverage is required when status is 'ok'")
        _require(_is_number(cov.get("percent")) and 0 <= cov["percent"] <= 100, "coverage.percent must be 0-100")
        _require(_is_count(cov.get("covered_lines")) and _is_count(cov.get("total_lines")), "coverage line counts must be non-negative integers")
        _require(cov["covered_lines"] <= cov["total_lines"], "coverage.covered_lines exceeds total_lines")
        missing = cov.get("missing_lines")
        _require(isinstance(missing, dict) and len(missing) <= MAX_ITEMS, "coverage.missing_lines must be an object")
        for path, lines in missing.items():
            _require(isinstance(path, str) and path, "coverage.missing_lines keys must be file paths")
            _require(isinstance(lines, list) and len(lines) <= 1_000_000 and all(_is_count(n) for n in lines),
                     f"coverage.missing_lines[{path!r}] must be a list of line numbers")

    mut = record.get("mutation")
    if mut is not None:
        _require(isinstance(mut, dict), "mutation must be an object or null")
        _require(all(_is_count(mut.get(k)) for k in ("killed", "survived", "total")), "mutation counts must be non-negative integers")
        _require(mut["killed"] + mut["survived"] == mut["total"], "mutation killed + survived != total")
        _require(_is_number(mut.get("score")) and 0 <= mut["score"] <= 100, "mutation.score must be 0-100")

    risk = record.get("risk")
    _require(isinstance(risk, list) and len(risk) <= MAX_ITEMS, "risk must be a list")
    for r in risk:
        _require(isinstance(r, dict) and isinstance(r.get("file"), str) and r["file"], "risk entries need a file")
        _require(_is_number(r.get("score")) and _is_count(r.get("rank")), "risk entries need a numeric score and integer rank")
        _require(isinstance(r.get("reasons"), list) and all(isinstance(x, str) for x in r["reasons"]), "risk reasons must be strings")
    _require(len({r["file"] for r in risk}) == len(risk), "risk has duplicate files")

    eps = record.get("endpoints")
    if eps is not None:
        _require(isinstance(eps, list) and len(eps) <= MAX_ITEMS, "endpoints must be a list or null")
        for e in eps:
            _require(isinstance(e, dict) and set(e) == {"file", "function", "method", "path", "has_test"}, "malformed endpoint entry")
            _require(all(isinstance(e[k], str) for k in ("file", "function", "method", "path")), "endpoint fields must be strings")
            _require(isinstance(e["has_test"], bool), "endpoint has_test must be a boolean")


def new_run_id() -> str:
    return str(uuid.uuid4())


def _posix(path: str) -> str:
    # Same file, same key on every OS: coverage.py reports native separators.
    return Path(path).as_posix()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"invalid run record: {message}")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _is_count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_canonical_uuid(value: str) -> bool:
    try:
        return str(uuid.UUID(value)) == value
    except ValueError:
        return False


def _timestamp(record: dict, key: str) -> datetime:
    value = record.get(key)
    try:
        parsed = datetime.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        parsed = None
    _require(parsed is not None and parsed.tzinfo is not None, f"{key} must be an ISO-8601 timestamp with a UTC offset")
    return parsed
