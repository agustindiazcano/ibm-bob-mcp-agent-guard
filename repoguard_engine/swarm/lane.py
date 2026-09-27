"""The lane state machine (Phase 18 S4, docs/MULTI_AGENT_SWARM.md Section 14
Step 4): WRITING(r) -> VERIFYING(r) -> ACCEPTED | NO_GAIN | FAILED, revising
to WRITING(r+1) while rounds remain. No critic step here -- that's S5.

"Best round wins": a lane may revise more than once trying to kill more
mutants; if a later round regresses (breaks the suite, or otherwise scores
worse), it must never replace an earlier, better round. Ranked by
(suite green, most kills, lowest round number), in that priority order.

Any exception anywhere inside a lane is caught here and turned into a
FAILED outcome -- one lane's bad day (a hallucinated tool call, a sandbox
hiccup) must never crash the run for every other lane (runner.py runs each
lane inside its own thread and its own try/except, but a lane can also be
driven directly, e.g. from a unit test or workers=1, so the guarantee lives
here, not only in the caller).
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from ..ai_providers import ChatProvider
from ..watson_agent.orchestrator import _run_chat_stage
from ..watson_agent.prompts import TEST_WRITER_PROMPT
from . import blackboard
from .guard import writer_toolset
from .plan import LanePlan
from .verify import VerifyResult, verify_lane


@dataclass
class LaneOutcome:
    module: str
    status: str  # ACCEPTED | NO_GAIN | FAILED
    round: int
    suite_passed: bool = False
    newly_killed: list[str] = field(default_factory=list)
    still_alive: list[str] = field(default_factory=list)
    test_sha256: str | None = None
    error: str | None = None


def owned_test_path(module: str) -> str:
    """The one file this lane may write. Uses the full relative path with
    separators turned into "_" to avoid collisions between same-named files
    in different packages (e.g. "shop/cart.py" -> "tests/test_shop_cart_swarm.py")."""
    stem = Path(module).with_suffix("").as_posix().replace("/", "_")
    return f"tests/test_{stem}_swarm.py"


def _rank(outcome: LaneOutcome) -> tuple[int, int, int]:
    passed = outcome.status != "FAILED"
    return (1 if passed else 0, len(outcome.newly_killed), -outcome.round)


def _better(current: LaneOutcome | None, candidate: LaneOutcome) -> LaneOutcome:
    if current is None or _rank(candidate) > _rank(current):
        return candidate
    return current


def _classify(vr: VerifyResult) -> str:
    if not vr.suite_passed or vr.regressed:
        return "FAILED"
    gained = bool(vr.newly_killed) or bool(vr.newly_covered)
    return "ACCEPTED" if gained else "NO_GAIN"


def _should_revise(vr: VerifyResult, round_n: int, rounds: int) -> bool:
    return round_n < rounds and (not vr.suite_passed or bool(vr.still_alive))


def _describe_mutants(records: list[dict]) -> str:
    lines = [
        f"  - line {r['lineno']} in {r['function']}: {r['description']}  | {r['original_line']}" for r in records
    ]
    return "\n".join(lines) or "  (none)"


def _writer_prompt(lane_plan: LanePlan, previous: LaneOutcome | None) -> str:
    survivors = [r for r in lane_plan.baseline_mutants if r["outcome"] == "survived"]
    parts = [
        f"File: {lane_plan.module}",
        f"Coverage gaps (missing lines): {lane_plan.missing_lines}",
        "Surviving mutants in this file:",
        _describe_mutants(survivors),
    ]
    if previous is not None and previous.still_alive:
        still = [r for r in lane_plan.baseline_mutants if r["fingerprint"] in previous.still_alive]
        parts += ["", "Still alive after your last attempt:", _describe_mutants(still)]
    parts.append(
        "\nRead this file, then write one pytest test file under tests/ that kills as "
        "many of the surviving mutants as possible."
    )
    return "\n".join(parts)


def run_lane(
    sandbox: Path,
    lane_plan: LanePlan,
    provider_factory: Callable[[], ChatProvider],
    rd: Path,
    timeline: blackboard.Timeline,
    mutation_pool,
    *,
    rounds: int = 2,
    mutation_workers: int = 1,
    lane_index: int = 0,
) -> LaneOutcome:
    module = lane_plan.module
    lane_id = f"lane-{lane_index}"
    owned = owned_test_path(module)
    timeline.event(lane_id, "runner", "lane_start", module=module)

    try:
        blackboard.write_task(
            rd,
            module,
            {
                "module": module,
                "owned_test_file": owned,
                "missing_lines": lane_plan.missing_lines,
                "surviving_mutants": [r for r in lane_plan.baseline_mutants if r["outcome"] == "survived"],
            },
        )
        baseline_outcomes = {r["fingerprint"]: r["outcome"] for r in lane_plan.baseline_mutants}
        provider = provider_factory()

        best: LaneOutcome | None = None
        round_n = 1
        while True:
            timeline.event(lane_id, "writer", "stage_start", round=round_n)
            schemas, registry = writer_toolset(sandbox, owned)
            stage = _run_chat_stage(
                provider,
                TEST_WRITER_PROMPT,
                _writer_prompt(lane_plan, best),
                str(sandbox),
                schemas=schemas,
                registry=registry,
            )
            blackboard.write_stage(
                rd,
                module,
                "writer",
                round_n,
                {"content": stage.content, "tool_calls": stage.tool_calls, "llm_calls": stage.llm_calls,
                 "wall_s": stage.wall_s},
            )
            owned_path = sandbox / owned
            written = owned_path.read_text(encoding="utf-8") if owned_path.is_file() else ""
            if written:
                blackboard.write_test_snapshot(rd, module, round_n, written)
            timeline.event(lane_id, "writer", "stage_end", round=round_n)

            timeline.event(lane_id, "verify", "stage_start", round=round_n)
            vr = verify_lane(
                sandbox,
                module,
                baseline_outcomes,
                lane_plan.missing_lines,
                mutation_workers=mutation_workers,
                executor=mutation_pool,
            )
            blackboard.write_stage(rd, module, "verify", round_n, dataclasses.asdict(vr))
            timeline.event(lane_id, "verify", "stage_end", round=round_n, suite_passed=vr.suite_passed)

            candidate = LaneOutcome(
                module=module,
                status=_classify(vr),
                round=round_n,
                suite_passed=vr.suite_passed,
                newly_killed=vr.newly_killed,
                still_alive=vr.still_alive,
            )
            best = _better(best, candidate)

            if not _should_revise(vr, round_n, rounds):
                break
            round_n += 1

        assert best is not None
        if best.status == "ACCEPTED":
            final_content = (sandbox / owned).read_text(encoding="utf-8")
            best.test_sha256 = blackboard.write_final_test(rd, module, final_content)

        blackboard.write_lane_result(
            rd,
            module,
            {
                "status": best.status,
                "round": best.round,
                "newly_killed": best.newly_killed,
                "still_alive": best.still_alive,
                "test_sha256": best.test_sha256,
                "owned_test_file": owned,
            },
        )
        timeline.event(lane_id, "runner", "lane_end", module=module, status=best.status)
        return best
    except Exception as exc:  # a bad tool call, a sandbox hiccup, anything -- never crash the run
        error = f"{type(exc).__name__}: {exc}"
        outcome = LaneOutcome(module=module, status="FAILED", round=0, error=error)
        try:
            blackboard.write_lane_result(rd, module, {"status": "FAILED", "round": 0, "error": error})
        except Exception:
            pass
        timeline.event(lane_id, "runner", "lane_end", module=module, status="FAILED", error=error)
        return outcome
