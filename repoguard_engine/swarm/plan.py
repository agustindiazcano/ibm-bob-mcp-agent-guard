"""Orchestrator: baseline measurement -> a lane plan (Phase 18 S4).

One lane per source file that has >=1 surviving mutant or >=1 uncovered
line -- no cap, unlike the sequential fix loop's MAX_FILES_PER_RUN. Also
snapshots a sha256 manifest of the real tests/ dir so a later fan-in (S6)
can detect if tests/ changed underneath a long-running swarm.
"""

from __future__ import annotations

import dataclasses
import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from ..pipeline import PipelineResult


def _posix(path: str) -> str:
    """coverage.py's missing_lines keys use OS-native separators;
    mutation.py's file keys are always posix (see
    watson_agent/orchestrator.py's describe_survivors). Normalize to posix
    everywhere a file is used as a join key across the two."""
    return Path(path).as_posix()


@dataclass
class LanePlan:
    module: str  # posix path relative to the repo, e.g. "shop/cart.py"
    survivors: int
    risk: float
    missing_lines: list[int] = field(default_factory=list)
    # Baseline per-mutant records for this file (dataclasses.asdict(MutantRecord)),
    # used both for the writer prompt and as the join key for the Verifier.
    baseline_mutants: list[dict] = field(default_factory=list)


@dataclass
class Plan:
    lanes: list[LanePlan] = field(default_factory=list)
    tests_manifest: dict[str, str] = field(default_factory=dict)  # relative posix path -> sha256 hex


def build_plan(baseline: PipelineResult, tests_dir: str = "tests") -> Plan:
    """One lane per file with >=1 surviving mutant OR >=1 uncovered line,
    sorted by (-survivors, -risk, path)."""
    risk_by_file = {_posix(r.file): r.score for r in baseline.risk}

    mutants_by_file: dict[str, list[dict]] = {}
    if baseline.mutation is not None:
        for record in baseline.mutation.mutants:
            mutants_by_file.setdefault(_posix(record.file), []).append(dataclasses.asdict(record))

    missing_by_file: dict[str, list[int]] = {}
    if baseline.gap is not None:
        for raw_file, lines in baseline.gap.missing_lines_by_file.items():
            if lines:
                missing_by_file[_posix(raw_file)] = list(lines)

    files = set(mutants_by_file) | set(missing_by_file)
    lanes: list[LanePlan] = []
    for module in files:
        records = mutants_by_file.get(module, [])
        survivors = [r for r in records if r["outcome"] == "survived"]
        if not survivors and not missing_by_file.get(module):
            continue
        lanes.append(
            LanePlan(
                module=module,
                survivors=len(survivors),
                risk=risk_by_file.get(module, 0.0),
                missing_lines=sorted(missing_by_file.get(module, [])),
                baseline_mutants=records,
            )
        )
    lanes.sort(key=lambda lane: (-lane.survivors, -lane.risk, lane.module))

    tests_manifest = _tests_manifest(Path(baseline.repo_path), tests_dir)
    return Plan(lanes=lanes, tests_manifest=tests_manifest)


def _tests_manifest(repo: Path, tests_dir: str) -> dict[str, str]:
    root = repo / tests_dir
    if not root.is_dir():
        return {}
    manifest: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            rel = path.relative_to(repo).as_posix()
            manifest[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return manifest
