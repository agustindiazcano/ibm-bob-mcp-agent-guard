"""The swarm Reporter (Phase 18 S6): watson-evidence/NN-swarm.md, numbered in
the same NN sequence as the sequential loop's NN-fix-loop.md, with the lane
table and per-phase wall times H1 (swarm vs sequential speed) needs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .run import SwarmResult


def write_swarm_evidence(repo: str | Path, result: SwarmResult) -> str:
    out_dir = Path(repo) / "watson-evidence"
    out_dir.mkdir(exist_ok=True)
    existing = sorted(out_dir.glob("[0-9][0-9]-*.md"))
    next_n = int(existing[-1].name[:2]) + 1 if existing else 1
    path = out_dir / f"{next_n:02d}-swarm.md"

    lane_rows = [
        f"| {o.module} | {o.status} | {o.round} / {o.rounds_run} | {len(o.newly_killed)} | "
        f"{o.verdict or '-'} | {o.llm_calls} | {o.wall_s:.1f} |"
        for o in result.lanes
    ]
    rejected = result.fanin.get("rejected") or {}
    sections = [
        f"# AI swarm fix loop -- {datetime.now(timezone.utc).isoformat()}",
        f"Repo: {result.repo_path}\n\nRun id: `{result.run_id}` (blackboard: `repoguard-out/swarm/{result.run_id}/`)",
        f"Status: **{result.status}** · Gate passed: {result.passed_gate} · Lanes in parallel: {result.workers}",
        "## Lanes\n\n| File | Status | Winning round / rounds run | New kills | Critic verdict | LLM calls | Wall s |\n"
        "|---|---|---|---|---|---|---|\n" + ("\n".join(lane_rows) or "| (no lanes) | | | | | | |"),
        "## Rejected at fan-in\n\n" + ("\n".join(f"- {m}: {r[:300]}" for m, r in rejected.items()) or "(none)"),
        "## Timing\n\n| Phase | Wall s |\n|---|---|\n"
        + "\n".join(f"| {phase} | {seconds:.1f} |" for phase, seconds in result.wall_s.items()),
        f"## Gate\n```json\n{json.dumps(result.gate, indent=2, default=str)}\n```",
        f"## Before\n```json\n{json.dumps(result.baseline, indent=2)}\n```",
        f"## After\n```json\n{json.dumps(result.after, indent=2)}\n```",
    ]
    if result.error:
        sections.insert(3, f"Error: `{result.error}`")
    path.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    return str(path)
