"""The lane Verifier (Phase 18 S4, docs/MULTI_AGENT_SWARM.md Section 4.3).

Runs inside a lane's sandbox after each writer round, in this order:
1. The full suite must pass on unmodified source -- if red, stop here and
   report a suite failure, not a mutation result (a red baseline would make
   core.run_mutation's own _check_baseline raise instead, several minutes
   later, for a failure we already know about).
2. Scoped mutation run on the lane's target file (all of its mutants, not
   only the ones that survived at baseline -- this also covers a swarm run
   overwriting an existing owned file from a previous run).
3. Coverage on the sandbox, for the lane's baseline-missing lines.
4. Join by the mutant's stable fingerprint against the baseline outcomes for
   this file (never by index -- a file-scoped run's mutant indices restart
   at 0 and don't match the whole-repo baseline's).
"""

from __future__ import annotations

from concurrent.futures import Executor
from dataclasses import dataclass, field
from pathlib import Path

from ..core import find_coverage_gaps, measure_coverage
from ..mutation import run_mutation
from ..watson_agent.tools import run_tests


@dataclass
class VerifyResult:
    suite_passed: bool
    newly_killed: list[str] = field(default_factory=list)  # fingerprints: survived at baseline, killed now
    still_alive: list[str] = field(default_factory=list)  # fingerprints: survived at baseline, survived now
    regressed: list[str] = field(default_factory=list)  # fingerprints: killed at baseline, survived now
    newly_covered: list[int] = field(default_factory=list)  # lines missing at baseline, covered now
    total_mutants: int = 0
    error: str | None = None


def verify_lane(
    sandbox: str | Path,
    module: str,
    baseline_fingerprint_outcomes: dict[str, str],
    baseline_missing_lines: list[int],
    *,
    tests_dir: str = "tests",
    mutation_workers: int = 1,
    executor: Executor | None = None,
) -> VerifyResult:
    sandbox = Path(sandbox)

    suite = run_tests(repo_path=str(sandbox))
    if not suite["passed"]:
        return VerifyResult(suite_passed=False, error=suite["output"])

    mutation = run_mutation(
        sandbox, paths_to_mutate=module, tests_dir=tests_dir, workers=mutation_workers, executor=executor
    )

    newly_killed: list[str] = []
    still_alive: list[str] = []
    regressed: list[str] = []
    for record in mutation.mutants:
        baseline_outcome = baseline_fingerprint_outcomes.get(record.fingerprint)
        if baseline_outcome is None:
            continue  # not seen at baseline (shouldn't happen -- source is unchanged); nothing to join against
        was_alive = baseline_outcome == "survived"
        is_alive = record.outcome == "survived"
        if was_alive and not is_alive:
            newly_killed.append(record.fingerprint)
        elif was_alive and is_alive:
            still_alive.append(record.fingerprint)
        elif not was_alive and is_alive:
            regressed.append(record.fingerprint)

    newly_covered = _newly_covered_lines(sandbox, module, baseline_missing_lines)

    return VerifyResult(
        suite_passed=True,
        newly_killed=newly_killed,
        still_alive=still_alive,
        regressed=regressed,
        newly_covered=newly_covered,
        total_mutants=mutation.total,
    )


def _newly_covered_lines(sandbox: Path, module: str, baseline_missing_lines: list[int]) -> list[int]:
    if not baseline_missing_lines:
        return []
    coverage = measure_coverage(sandbox)
    gaps = find_coverage_gaps(coverage, repo_path=str(sandbox))
    still_missing = {
        line for raw_file, lines in gaps.missing_lines_by_file.items() if Path(raw_file).as_posix() == module for line in lines
    }
    return sorted(set(baseline_missing_lines) - still_missing)
