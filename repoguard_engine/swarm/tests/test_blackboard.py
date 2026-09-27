"""Unit tests for repoguard_engine/swarm/blackboard.py (Phase 18 S4).

No lane.py/runner.py involved -- these exercise the blackboard file contract
in isolation: schema tagging, the atomic tmp+replace write pattern, the
.test.py.txt-only guard on test snapshots, and Timeline's thread safety.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from repoguard_engine.swarm import blackboard


@pytest.fixture
def rd(tmp_path: Path) -> Path:
    return blackboard.run_dir(tmp_path, "run-1")


# ---------------------------------------------------------------------------
# schema tagging
# ---------------------------------------------------------------------------

def test_write_plan_tags_schema(rd: Path) -> None:
    blackboard.write_plan(rd, {"lanes": ["shop/cart.py"]})
    data = json.loads((rd / "plan.json").read_text(encoding="utf-8"))
    assert data["schema"] == "repoguard.swarm.plan/v1"
    assert data["lanes"] == ["shop/cart.py"]


def test_write_task_tags_schema(rd: Path) -> None:
    blackboard.write_task(rd, "shop/cart.py", {"module": "shop/cart.py"})
    data = json.loads((rd / "lanes" / "shop_cart.py" / "task.json").read_text(encoding="utf-8"))
    assert data["schema"] == "repoguard.swarm.task/v1"


@pytest.mark.parametrize("stage", ["writer", "verify", "critic"])
def test_write_stage_tags_schema_per_kind(rd: Path, stage: str) -> None:
    blackboard.write_stage(rd, "shop/cart.py", stage, 1, {"x": 1})
    data = blackboard.read_stage(rd, "shop/cart.py", stage, 1)
    assert data is not None
    assert data["schema"] == f"repoguard.swarm.{stage}/v1"


def test_write_stage_rejects_unknown_kind(rd: Path) -> None:
    with pytest.raises(ValueError, match="stage must be one of"):
        blackboard.write_stage(rd, "shop/cart.py", "bogus", 1, {})


def test_read_stage_missing_returns_none(rd: Path) -> None:
    assert blackboard.read_stage(rd, "shop/cart.py", "writer", 1) is None


def test_write_lane_result_tags_schema_and_validates_status(rd: Path) -> None:
    blackboard.write_lane_result(rd, "shop/cart.py", {"status": "ACCEPTED"})
    data = json.loads((rd / "lanes" / "shop_cart.py" / "result.json").read_text(encoding="utf-8"))
    assert data["schema"] == "repoguard.swarm.result/v1"

    with pytest.raises(ValueError, match="status"):
        blackboard.write_lane_result(rd, "shop/cart.py", {"status": "WHATEVER"})


def test_write_gate_tags_schema(rd: Path) -> None:
    blackboard.write_gate(rd, {"passed": True})
    data = json.loads((rd / "gate.json").read_text(encoding="utf-8"))
    assert data["schema"] == "repoguard.swarm.gate/v1"


# ---------------------------------------------------------------------------
# atomic writes
# ---------------------------------------------------------------------------

def test_atomic_write_leaves_target_untouched_if_replace_never_happens(rd: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(blackboard.os, "replace", lambda *_a, **_kw: None)
    blackboard.write_plan(rd, {"lanes": []})

    target = rd / "plan.json"
    tmp = rd / "plan.json.tmp"
    assert not target.exists(), "target must not exist until os.replace actually runs"
    assert tmp.exists(), "content should have been staged in the .tmp file first"
    assert json.loads(tmp.read_text(encoding="utf-8"))["schema"] == "repoguard.swarm.plan/v1"


def test_atomic_write_produces_target_when_replace_runs(rd: Path) -> None:
    blackboard.write_gate(rd, {"passed": False})
    assert (rd / "gate.json").exists()
    assert not (rd / "gate.json.tmp").exists()


# ---------------------------------------------------------------------------
# .test.py.txt snapshot guard
# ---------------------------------------------------------------------------

def test_write_snapshot_rejects_non_test_py_txt_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"\.test\.py\.txt"):
        blackboard._write_snapshot(tmp_path / "sneaky.py", "def test_x(): assert True\n")
    assert not (tmp_path / "sneaky.py").exists()


def test_write_snapshot_accepts_test_py_txt_path(tmp_path: Path) -> None:
    path = tmp_path / "writer-1.test.py.txt"
    blackboard._write_snapshot(path, "def test_x(): assert True\n")
    assert path.read_text(encoding="utf-8") == "def test_x(): assert True\n"


def test_write_test_snapshot_and_final_test(rd: Path) -> None:
    content = "def test_x():\n    assert True\n"
    path = blackboard.write_test_snapshot(rd, "shop/cart.py", 1, content)
    assert path.name == "writer-1.test.py.txt"
    assert path.read_text(encoding="utf-8") == content

    digest = blackboard.write_final_test(rd, "shop/cart.py", content)
    final_path = rd / "lanes" / "shop_cart.py" / "final.test.py.txt"
    assert final_path.read_text(encoding="utf-8") == content
    import hashlib

    assert digest == hashlib.sha256(content.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Timeline concurrency
# ---------------------------------------------------------------------------

def test_timeline_event_from_many_threads_produces_n_valid_lines(rd: Path) -> None:
    timeline = blackboard.Timeline(rd)
    n = 50
    barrier = threading.Barrier(n)

    def worker(i: int) -> None:
        barrier.wait()
        timeline.event(f"lane-{i}", "runner", "stage_start", round=1)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    lines = (rd / "timeline.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == n
    parsed = [json.loads(line) for line in lines]  # raises if any line is truncated/interleaved
    assert {p["lane"] for p in parsed} == {f"lane-{i}" for i in range(n)}
