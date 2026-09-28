"""run_swarm: the whole multi-agent fix loop (Phase 18 S6,
docs/MULTI_AGENT_SWARM.md Sections 4.5 and 14 Step 6).

baseline -> plan (one lane per file) -> lanes in parallel (writer ->
Verifier -> critic, up to `rounds`) -> fan-in -> one global Gate re-measure
-> Publisher -> Reporter.

The Gate's run_pipeline on the merged repo is the only measurement reported
as the result (AGENTS.md Section 4: the AI decides, the engine measures);
per-lane numbers and the union of lane kills are recorded as attribution
only. Pass = green suite (run_mutation's own baseline guard raises
otherwise) + coverage >= threshold + killed > baseline.killed + no mutant
that was killed at baseline surviving now. If the Gate raises, fan-in's
writes are rolled back so the real tests/ is left exactly as it was.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ..ai_providers import ChatProvider
from ..pipeline import PipelineResult, run_pipeline
from ..watson_agent.orchestrator import _publish
from . import blackboard
from .fanin import FanInResult, fan_in, rollback
from .lane import LaneOutcome, owned_test_path
from .plan import build_plan
from .providers import role_provider_factory
from .report import write_swarm_evidence
from .runner import run_lanes

DEFAULT_MAX_WORKERS = 4


@dataclass
class SwarmResult:
    repo_path: str
    run_id: str
    baseline: dict
    after: dict | None = None
    lanes: list[LaneOutcome] = field(default_factory=list)
    fanin: dict = field(default_factory=dict)
    gate: dict = field(default_factory=dict)
    files: list[dict] = field(default_factory=list)  # {"path", "status": added|modified, "content"}
    status: str = "error"  # accepted | partial | rejected | error, same vocabulary as FixResult
    passed_gate: bool = False
    published: bool = False
    evidence_path: str | None = None
    error: str | None = None
    workers: int = 0
    wall_s: dict[str, float] = field(default_factory=dict)


def run_swarm(
    repo_path: str | Path,
    *,
    gate_threshold: float = 80.0,
    publish: bool = False,
    provider: str | None = None,
    model_id: str | None = None,
    provider_factory: Callable[[str], ChatProvider] | None = None,
    workers: int | None = None,
    rounds: int = 2,
    mutation_workers: int | None = None,
    on_event: Callable[[str, dict], None] | None = None,
    run_id: str | None = None,
) -> SwarmResult:
    """Run the swarm fix loop on repo_path, in place (callers that must not
    touch the target -- web/fix_job.py -- pass a temp copy, as they already
    do for run_fix_loop). Writes repoguard-out/swarm/<run_id>/ (blackboard,
    gate.json) and watson-evidence/NN-swarm.md.

    provider_factory: an explicit factory(role) -> ChatProvider (tests pass
    a ScriptedProvider here); otherwise swarm/providers.py builds one from
    provider/model_id, failing on missing credentials before any measuring.
    workers: lanes in parallel (default min(lanes, 4)). mutation_workers:
    one shared pool for every mutation run, baseline and Gate included.
    on_event(type, data): progress only, never changes what the run does.
    """
    started = time.perf_counter()
    emit = on_event or (lambda _type, _data: None)
    factory = provider_factory or role_provider_factory(provider, model_id)
    mutation_workers = mutation_workers or os.cpu_count() or 1
    repo = Path(repo_path).resolve()
    run_id = run_id or f"swarm-{datetime.now(timezone.utc):%Y%m%d%H%M%S}"

    emit("baseline_start", {})
    phase = time.perf_counter()
    baseline = _measure(repo, gate_threshold, mutation_workers)
    plan = build_plan(baseline)
    result = SwarmResult(repo_path=str(repo), run_id=run_id, baseline=baseline.dashboard)
    result.wall_s["baseline"] = time.perf_counter() - phase
    rd = blackboard.run_dir(repo, run_id)
    emit("baseline_done", {"dashboard": baseline.dashboard, "files": [lane.module for lane in plan.lanes], "run_id": run_id})

    try:
        if not plan.lanes:
            return _finish_unchanged(result, baseline, rd, "no file has a surviving mutant or a coverage gap")

        result.workers = workers or min(len(plan.lanes), DEFAULT_MAX_WORKERS)
        phase = time.perf_counter()
        lanes = run_lanes(
            repo, plan, factory, run_id=run_id, workers=result.workers, rounds=rounds,
            mutation_workers=mutation_workers, on_event=lambda record: emit("lane", record),
        )
        result.lanes = lanes.lanes
        result.wall_s["lanes"] = time.perf_counter() - phase

        emit("fanin_start", {})
        phase = time.perf_counter()
        fanin = fan_in(repo, plan, result.lanes, rd)
        _mark_rejected(result.lanes, fanin, rd)
        result.fanin = {"merged": fanin.merged, "rejected": fanin.rejected, "stability": fanin.stability}
        result.wall_s["fanin"] = time.perf_counter() - phase
        emit("fanin_done", result.fanin)
        if not fanin.merged:
            return _finish_unchanged(result, baseline, rd, "no lane's test file survived fan-in")

        emit("remeasure_start", {})
        phase = time.perf_counter()
        try:
            after = _measure(repo, gate_threshold, mutation_workers)
        except Exception as exc:
            rollback(repo, fanin)
            result.error = f"{type(exc).__name__}: {exc}"
            result.gate = {"error": result.error, "rolled_back": fanin.written}
            blackboard.write_gate(rd, result.gate)
            result.wall_s["gate"] = time.perf_counter() - phase
            return result
        result.wall_s["gate"] = time.perf_counter() - phase
        _judge(result, baseline, after, fanin)
        blackboard.write_gate(rd, result.gate)
        emit("remeasure_done", {"dashboard": after.dashboard, "passed_gate": result.passed_gate})

        if publish and result.status == "accepted":
            _publish(str(repo))
            result.published = True
        return result
    finally:
        result.wall_s["total"] = time.perf_counter() - started
        result.evidence_path = write_swarm_evidence(repo, result)


def _measure(repo: Path, gate_threshold: float, mutation_workers: int) -> PipelineResult:
    # persist=False: same reason as run_fix_loop -- a before/after pair isn't
    # two unrelated runs, and web Autofix runs on a temp copy.
    return run_pipeline(
        repo, include_mutation=True, include_endpoints=True, gate_threshold=gate_threshold,
        mutation_workers=mutation_workers, persist=False,
    )


def _finish_unchanged(result: SwarmResult, baseline: PipelineResult, rd: Path, reason: str) -> SwarmResult:
    result.after = baseline.dashboard
    result.status = "rejected"
    result.gate = {"skipped": reason}
    blackboard.write_gate(rd, result.gate)
    return result


def _mark_rejected(lanes: list[LaneOutcome], fanin: FanInResult, rd: Path) -> None:
    for outcome in lanes:
        reason = fanin.rejected.get(outcome.module)
        if reason is None:
            continue
        outcome.status = "REJECTED_AT_FANIN"
        outcome.error = reason
        blackboard.write_lane_result(
            rd, outcome.module,
            {"status": "REJECTED_AT_FANIN", "round": outcome.round, "reason": reason,
             "owned_test_file": owned_test_path(outcome.module), "test_sha256": outcome.test_sha256},
        )


def _judge(result: SwarmResult, baseline: PipelineResult, after: PipelineResult, fanin: FanInResult) -> None:
    """Decide the Gate from the two engine measurements only, and record
    per-file attribution (informational, never pass/fail)."""
    assert baseline.mutation is not None and after.mutation is not None
    before_outcomes = {m.fingerprint: m.outcome for m in baseline.mutation.mutants}
    regressions = sorted(
        m.fingerprint for m in after.mutation.mutants
        if m.outcome == "survived" and before_outcomes.get(m.fingerprint, "survived") != "survived"
    )
    killed_gain = after.mutation.killed - baseline.mutation.killed

    result.after = after.dashboard
    result.passed_gate = after.passed_gate and killed_gain > 0 and not regressions
    if not result.passed_gate:
        result.status = "rejected"
    elif fanin.rejected or any(o.status != "ACCEPTED" for o in result.lanes):
        result.status = "partial"
    else:
        result.status = "accepted"

    result.files = [
        {"path": rel, "status": "modified" if rel in fanin.overwritten else "added",
         "content": (Path(result.repo_path) / rel).read_text(encoding="utf-8")}
        for rel in fanin.written
    ]
    result.gate = {
        "passed": result.passed_gate,
        "status": result.status,
        "coverage_threshold": after.gate_threshold,
        "coverage_passed": after.passed_gate,
        "baseline": _numbers(baseline),
        "after": _numbers(after),
        "killed_gain": killed_gain,
        "regressions": regressions,
        "outcome_counts": after.mutation.outcome_counts(),
        "lane_kills_union": sum(len(o.newly_killed) for o in result.lanes if o.module in fanin.merged),
        "attribution": _attribution(baseline, after, result.lanes),
        "merged": fanin.written,
    }


def _numbers(run: PipelineResult) -> dict:
    assert run.mutation is not None and run.coverage is not None
    return {
        "coverage": run.coverage.percent,
        "mutation_score": run.mutation.score,
        "killed": run.mutation.killed,
        "total": run.mutation.total,
        "surviving": sorted(m.fingerprint for m in run.mutation.mutants if m.outcome == "survived"),
    }


def _attribution(baseline: PipelineResult, after: PipelineResult, lanes: list[LaneOutcome]) -> list[dict]:
    assert baseline.mutation is not None and after.mutation is not None

    def killed_in(run_mutants, module: str) -> int:
        return sum(1 for m in run_mutants if m.file == module and m.outcome != "survived")

    rows = []
    for outcome in lanes:
        base = killed_in(baseline.mutation.mutants, outcome.module)
        rows.append({
            "module": outcome.module,
            "status": outcome.status,
            "baseline_killed": base,
            "lane_isolated_killed": base + len(outcome.newly_killed),
            "gate_killed": killed_in(after.mutation.mutants, outcome.module),
        })
    return rows
