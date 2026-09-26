"""watsonx.ai fix loop: measure -> prioritize -> write tests -> critic ->
gate -> optional publish -> evidence report.

This is the direct functional replacement for .bob/custom_modes.yaml's
Orchestrator / Test Writer / Critic / Gate / Publisher modes, now retired
(see .bob/DEPRECATED.md). Runs in-process against pipeline.run_pipeline, not
through an MCP round-trip -- same layering rule as web/server.py (AGENTS.md
Section 4: "cli.py, mcp_server.py and web/server.py are thin adapters over
pipeline/core").
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ..pipeline import run_pipeline
from .client import get_chat_model
from .prompts import CRITIC_PROMPT, TEST_WRITER_PROMPT
from .tools import TOOL_REGISTRY, TOOL_SCHEMAS, SourceEditRejected

MAX_FILES_PER_RUN = 3
MAX_TOOL_ROUNDS_PER_STAGE = 6
_SUBPROCESS_TIMEOUT = 60


@dataclass
class FixResult:
    repo_path: str
    baseline: dict
    after: dict | None = None
    files_attempted: list[str] = field(default_factory=list)
    critic_notes: list[str] = field(default_factory=list)
    published: bool = False
    evidence_path: str | None = None


def _priority_files(risk: list) -> list[str]:
    """Files to target this run, ranked by the already-computed risk score --
    never re-derive a priority order independently of core.compute_risk."""
    return [r.file for r in risk[:MAX_FILES_PER_RUN]]


def _run_chat_stage(model, system_prompt: str, user_prompt: str, repo_path: str) -> str:
    """One watsonx.ai chat-with-tools stage, looping on tool calls until the
    model returns plain content or the round-trip cap is hit."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for _ in range(MAX_TOOL_ROUNDS_PER_STAGE):
        response = model.chat(messages=messages, tools=TOOL_SCHEMAS)
        message = response["choices"][0]["message"]
        messages.append(message)
        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            return message.get("content", "") or ""

        for call in tool_calls:
            name = call["function"]["name"]
            try:
                args = json.loads(call["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {}
            args["repo_path"] = repo_path
            try:
                result = TOOL_REGISTRY[name](**args)
            except SourceEditRejected as exc:
                result = {"error": str(exc)}
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id", name),
                    "content": json.dumps(result, default=str),
                }
            )

    return "(stopped: exceeded tool-call round trip limit for this stage)"


def run_fix_loop(
    repo_path: str,
    *,
    gate_threshold: float = 80.0,
    publish: bool = False,
) -> FixResult:
    """
    Run the full watsonx.ai fix loop against repo_path.

    1. Measure a real baseline (coverage, gaps, mutation, risk).
    2. Prioritize up to MAX_FILES_PER_RUN files by risk score.
    3. Per file: watsonx.ai reads the source and writes a killing test via
       write_test_file (hard-guarded to tests/ only).
    4. A second watsonx.ai call critiques the new test.
    5. Re-measure for real (deterministic, no LLM involved) and gate.
    6. If publish=True and the gate passes, commit and open a PR.
    7. Write an evidence report to watson-evidence/.

    Raises WatsonxCredentialsError immediately if WATSONX_APIKEY /
    WATSONX_PROJECT_ID aren't set -- checked before the (multi-minute)
    mutation baseline runs, not after, so a missing-credentials failure is
    instant rather than waiting on a measurement that was going to be thrown
    away anyway.
    """
    model = get_chat_model()

    repo = str(Path(repo_path).resolve())
    baseline = run_pipeline(repo, include_mutation=True, include_endpoints=True, gate_threshold=gate_threshold)
    result = FixResult(repo_path=repo, baseline=baseline.dashboard)

    for file_rel in _priority_files(baseline.risk):
        result.files_attempted.append(file_rel)

        writer_prompt = (
            f"File: {file_rel}\n"
            f"Coverage gaps (missing lines): {baseline.gap.missing_lines_by_file.get(file_rel, []) if baseline.gap else []}\n"
            f"Surviving mutant IDs: {baseline.mutation.surviving_mutant_ids if baseline.mutation else []}\n\n"
            "Read this file, then write one pytest test file under tests/ "
            "that kills as many of the surviving mutants as possible."
        )
        _run_chat_stage(model, TEST_WRITER_PROMPT, writer_prompt, repo)

        critic_prompt = f"Review whatever test file(s) were just written for {file_rel}."
        notes = _run_chat_stage(model, CRITIC_PROMPT, critic_prompt, repo)
        result.critic_notes.append(f"{file_rel}: {notes}")

    after = run_pipeline(repo, include_mutation=True, include_endpoints=True, gate_threshold=gate_threshold)
    result.after = after.dashboard

    if publish and after.passed_gate:
        _publish(repo)
        result.published = True

    result.evidence_path = _write_evidence(repo, result)
    return result


def _publish(repo_path: str) -> None:
    """Branch, commit tests/ only, push, open a PR. Bare git/gh, like a human
    would run them -- same intentional exception as verify.py's phase0 check."""
    branch = f"fix/watsonx-{datetime.now(timezone.utc):%Y%m%d%H%M%S}"
    steps = [
        ["git", "checkout", "-b", branch],
        ["git", "add", "tests"],
        ["git", "commit", "-m", "test: watsonx.ai fix loop"],
        ["git", "push", "-u", "origin", branch],
        ["gh", "pr", "create", "--fill"],
    ]
    for step in steps:
        subprocess.run(step, cwd=repo_path, check=True, timeout=_SUBPROCESS_TIMEOUT)


def _write_evidence(repo_path: str, result: FixResult) -> str:
    """Plain Python, run at the end of the loop we already control -- no
    Stop-hook/event system needed the way .bob/hooks/evidence-export.mjs
    needed one inside Bob's IDE."""
    out_dir = Path(repo_path) / "watson-evidence"
    out_dir.mkdir(exist_ok=True)
    existing = sorted(out_dir.glob("[0-9][0-9]-*.md"))
    next_n = int(existing[-1].name[:2]) + 1 if existing else 1
    path = out_dir / f"{next_n:02d}-fix-loop.md"
    path.write_text(
        f"# watsonx.ai fix loop -- {datetime.now(timezone.utc).isoformat()}\n\n"
        f"Repo: {result.repo_path}\n\n"
        f"Files attempted: {', '.join(result.files_attempted) or '(none)'}\n\n"
        f"## Before\n```json\n{json.dumps(result.baseline, indent=2)}\n```\n\n"
        f"## After\n```json\n{json.dumps(result.after, indent=2)}\n```\n\n"
        "## Critic notes\n" + "\n\n".join(result.critic_notes),
        encoding="utf-8",
    )
    return str(path)
