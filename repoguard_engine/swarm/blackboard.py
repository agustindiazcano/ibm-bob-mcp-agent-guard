"""Read/write the swarm's communication contract (Phase 18 S4, see
docs/MULTI_AGENT_SWARM.md Section 6).

Agents don't share memory; they communicate through files under
    <target-repo>/repoguard-out/swarm/<run_id>/
so every run is auditable and a round-2 writer prompt can be rebuilt purely
by reading round 1's files back from disk.

Two real hazards fixed here, both required (Section 6):
- `core.run_mutation(".")` scans every .py file under the repo root, so a
  lane's draft test snapshotted with a real .py extension would become a
  mutation target itself and change the Gate's total count. Test-file
  snapshots are therefore written with a `.test.py.txt` extension, never
  `.py` -- enforced by _require_snapshot_path, not just a naming
  convention followed by callers.
- `_common.COPY_IGNORE` already excludes "repoguard-out" wholesale from
  every copytree (mutation copies, lane sandboxes), so the blackboard
  directory living under it is already excluded; nothing to add there.

Every JSON file carries a "schema": "repoguard.swarm.<kind>/v1" field,
merged in by the writer function itself -- callers never add it manually.
Every write is atomic (write "<path>.tmp", then os.replace, atomic on the
same volume including Windows). The only file with concurrent writers is
timeline.jsonl, guarded by one threading.Lock per Timeline instance.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

_SCHEMA_VERSION = "v1"
_SNAPSHOT_SUFFIX = ".test.py.txt"
_STAGE_KINDS = {"writer", "verify", "critic"}
_RESULT_STATUSES = {"ACCEPTED", "NO_GAIN", "BLOCKED", "FAILED", "REJECTED_AT_FANIN"}


def _safe_module_name(module: str) -> str:
    """A source file's posix path (e.g. "shop/cart.py") turned into a single
    directory-name-safe component, matching swarm/lane.py's owned-test-path
    naming so the two stay visually associated. The ".py" suffix is dropped:
    a directory named "shop_api.py" matches every rglob("*.py") the engine
    runs over the repo (api_check.py's endpoint scan read it as a file)."""
    return Path(module.replace("\\", "/")).with_suffix("").as_posix().replace("/", "_")


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def _atomic_write_json(path: Path, data: dict) -> None:
    _atomic_write_text(path, json.dumps(data, indent=2, default=str))


def _require_snapshot_path(path: Path) -> None:
    if not path.name.endswith(_SNAPSHOT_SUFFIX):
        raise ValueError(
            f"test snapshot path must end with {_SNAPSHOT_SUFFIX!r} (never .py -- "
            f"it would become a mutation target), got {path}"
        )


def _write_snapshot(path: Path, content: str) -> None:
    _require_snapshot_path(path)
    _atomic_write_text(path, content)


def _with_schema(data: dict, kind: str) -> dict:
    return {**data, "schema": f"repoguard.swarm.{kind}/{_SCHEMA_VERSION}"}


def run_dir(repo: str | Path, run_id: str) -> Path:
    rd = Path(repo) / "repoguard-out" / "swarm" / run_id
    rd.mkdir(parents=True, exist_ok=True)
    return rd


def _lane_dir(rd: Path, module: str) -> Path:
    d = Path(rd) / "lanes" / _safe_module_name(module)
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_plan(rd: Path, plan: dict) -> None:
    _atomic_write_json(Path(rd) / "plan.json", _with_schema(plan, "plan"))


def write_task(rd: Path, module: str, task: dict) -> None:
    _atomic_write_json(_lane_dir(rd, module) / "task.json", _with_schema(task, "task"))


def write_stage(rd: Path, module: str, stage: str, round_n: int, data: dict) -> None:
    if stage not in _STAGE_KINDS:
        raise ValueError(f"stage must be one of {sorted(_STAGE_KINDS)}, got {stage!r}")
    path = _lane_dir(rd, module) / f"{stage}-{round_n}.json"
    _atomic_write_json(path, _with_schema(data, stage))


def read_stage(rd: Path, module: str, stage: str, round_n: int) -> dict | None:
    path = _lane_dir(rd, module) / f"{stage}-{round_n}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_test_snapshot(rd: Path, module: str, round_n: int, content: str) -> Path:
    path = _lane_dir(rd, module) / f"writer-{round_n}{_SNAPSHOT_SUFFIX}"
    _write_snapshot(path, content)
    return path


def read_test_snapshot(rd: Path, module: str, round_n: int) -> str | None:
    path = _lane_dir(rd, module) / f"writer-{round_n}{_SNAPSHOT_SUFFIX}"
    return path.read_text(encoding="utf-8") if path.is_file() else None


def read_final_test(rd: Path, module: str) -> str | None:
    path = _lane_dir(rd, module) / f"final{_SNAPSHOT_SUFFIX}"
    return path.read_text(encoding="utf-8") if path.is_file() else None


def write_final_test(rd: Path, module: str, content: str) -> str:
    """Write the lane's final accepted test content and return its sha256
    hex digest (recorded in result.json so fan-in can check it unchanged)."""
    path = _lane_dir(rd, module) / f"final{_SNAPSHOT_SUFFIX}"
    _write_snapshot(path, content)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def write_lane_result(rd: Path, module: str, result: dict) -> None:
    status = result.get("status")
    if status not in _RESULT_STATUSES:
        raise ValueError(f"result['status'] must be one of {sorted(_RESULT_STATUSES)}, got {status!r}")
    _atomic_write_json(_lane_dir(rd, module) / "result.json", _with_schema(result, "result"))


def write_gate(rd: Path, gate: dict) -> None:
    _atomic_write_json(Path(rd) / "gate.json", _with_schema(gate, "gate"))


class Timeline:
    """Append-only timeline.jsonl, the one blackboard file with concurrent
    writers (one lane thread each). One shared instance per run; `event`
    guards the append with a lock so concurrent calls each produce exactly
    one complete, non-interleaved JSON line."""

    def __init__(self, rd: Path, listener: Callable[[dict], None] | None = None) -> None:
        self._path = Path(rd) / "timeline.jsonl"
        self._lock = threading.Lock()
        self._listener = listener

    def event(self, lane: str, agent: str, kind: str, **fields: object) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "lane": lane,
            "agent": agent,
            "kind": kind,
            **fields,
        }
        line = json.dumps(record, default=str) + "\n"
        with self._lock:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(line)
            if self._listener is not None:
                try:
                    self._listener(record)
                except Exception:
                    pass  # a broken progress listener must never fail a lane
