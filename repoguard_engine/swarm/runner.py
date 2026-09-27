"""ThreadPool fan-out over the swarm's lanes (Phase 18 S4).

All lane sandboxes are created serially, up front, before any lane starts
running, so a copytree never races a blackboard write. One shared mutation
pool is passed to every lane's Verifier, capping concurrent pytest
processes at mutation_workers total rather than workers * mutation_workers
(a nested-pool blowup). Lanes themselves run in a ThreadPoolExecutor;
sandbox cleanup is guaranteed via ExitStack regardless of how the run ends.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path

from ..ai_providers import ChatProvider
from . import blackboard
from .lane import LaneOutcome, run_lane
from .plan import Plan
from .sandbox import lane_sandbox


@dataclass
class RunResult:
    run_id: str
    lanes: list[LaneOutcome] = field(default_factory=list)


def run_lanes(
    repo: str | Path,
    plan: Plan,
    provider_factory: Callable[[], ChatProvider],
    *,
    run_id: str,
    workers: int = 4,
    rounds: int = 2,
    mutation_workers: int | None = None,
) -> RunResult:
    repo = Path(repo).resolve()
    mutation_workers = mutation_workers or os.cpu_count() or 1
    rd = blackboard.run_dir(repo, run_id)
    blackboard.write_plan(rd, {"lanes": [lane.module for lane in plan.lanes], "tests_manifest": plan.tests_manifest})
    timeline = blackboard.Timeline(rd)

    outcomes: dict[str, LaneOutcome] = {}
    with ExitStack() as stack:
        sandboxes = {
            lane.module: stack.enter_context(lane_sandbox(repo, f"lane-{i}")) for i, lane in enumerate(plan.lanes)
        }

        with (
            ThreadPoolExecutor(max_workers=mutation_workers, thread_name_prefix="repoguard-swarm-mutant") as mutation_pool,
            ThreadPoolExecutor(max_workers=workers, thread_name_prefix="repoguard-swarm-lane") as pool,
        ):
            futures = {
                pool.submit(
                    run_lane,
                    sandboxes[lane.module],
                    lane,
                    provider_factory,
                    rd,
                    timeline,
                    mutation_pool,
                    rounds=rounds,
                    mutation_workers=mutation_workers,
                    lane_index=i,
                ): lane.module
                for i, lane in enumerate(plan.lanes)
            }
            for future, module in futures.items():
                try:
                    outcomes[module] = future.result()
                except Exception as exc:  # run_lane already catches its own errors; this is a last resort
                    outcomes[module] = LaneOutcome(
                        module=module, status="FAILED", round=0, error=f"{type(exc).__name__}: {exc}"
                    )

    return RunResult(run_id=run_id, lanes=[outcomes[lane.module] for lane in plan.lanes])
