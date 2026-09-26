"""AI fix loop: measure -> prioritize -> write tests -> critic -> gate ->
optional publish -> evidence report.

This is the direct functional replacement for .bob/custom_modes.yaml's
Orchestrator / Test Writer / Critic / Gate / Publisher modes, now retired
(see .bob/DEPRECATED.md). Runs in-process against pipeline.run_pipeline, not
through an MCP round-trip -- same layering rule as web/server.py (AGENTS.md
Section 4: "cli.py, mcp_server.py and web/server.py are thin adapters over
pipeline/core").

Provider-agnostic: drives whichever ai_providers.get_provider() returns
(Vertex AI by default, or watsonx.ai via REPOGUARD_AI_PROVIDER=watsonx) --
see docs/MULTICLOUD_AI.md.
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ..ai_providers import ChatProvider, get_provider
from ..pipeline import run_pipeline
from .prompts import CRITIC_PROMPT, TEST_WRITER_PROMPT
from .tools import TOOL_REGISTRY, TOOL_SCHEMAS, SourceEditRejected

MAX_FILES_PER_RUN = 3
# read -> write -> run_tests -> (rewrite -> run_tests)* needs more headroom
# than the old write-once flow; 6 was tight even for one correction cycle.
MAX_TOOL_ROUNDS_PER_STAGE = 10
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
    # Wall-clock seconds per stage (baseline, each writer/critic call,
    # re-measure) and in total -- the timing baseline Phase 18's H1
    # (swarm faster than sequential) is measured against.
    timings: list[dict] = field(default_factory=list)
    wall_s: float | None = None
    # Stored before/after runs and their link, when persistence is on.
    fix_session_id: str | None = None


@dataclass
class StageResult:
    """What one chat-with-tools stage produced: the model's final text, the
    tool calls it made (name + parsed args, in order), and its wall time."""
    content: str
    tool_calls: list[dict] = field(default_factory=list)
    wall_s: float = 0.0


def describe_survivors(mutation, file_rel: str) -> str:
    """One line per surviving mutant in file_rel -- line, function, what
    changed, the original source line -- instead of bare positional IDs the
    writer can't map back to code."""
    if mutation is None:
        return "  (mutation not measured)"
    target = Path(file_rel).as_posix()  # coverage.py reports OS-native separators
    lines = [
        f"  - line {m.lineno} in {m.function}: {m.description}  | {m.original_line}"
        for m in mutation.mutants
        if m.file == target and m.outcome == "survived"
    ]
    return "\n".join(lines) or "  (none -- every mutant in this file is already killed)"


def _priority_files(risk: list) -> list[str]:
    """Files to target this run, ranked by the already-computed risk score --
    never re-derive a priority order independently of core.compute_risk."""
    return [r.file for r in risk[:MAX_FILES_PER_RUN]]


def _run_chat_stage(
    model,
    system_prompt: str,
    user_prompt: str,
    repo_path: str,
    *,
    schemas: list[dict] = TOOL_SCHEMAS,
    registry: dict = TOOL_REGISTRY,
) -> StageResult:
    """One chat-with-tools stage against the configured AI provider, looping
    on tool calls until the model returns plain content or the round-trip
    cap is hit. schemas/registry default to the full guarded toolset; a
    caller can pass a narrower one (e.g. a read-only critic)."""
    started = time.perf_counter()
    calls_made: list[dict] = []
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for _ in range(MAX_TOOL_ROUNDS_PER_STAGE):
        response = model.chat(messages=messages, tools=schemas)
        message = response["choices"][0]["message"]
        messages.append(message)
        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            return StageResult(message.get("content", "") or "", calls_made, time.perf_counter() - started)

        for call in tool_calls:
            name = call["function"]["name"]
            try:
                args = json.loads(call["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {}
            calls_made.append({"name": name, "args": dict(args)})
            args["repo_path"] = repo_path
            try:
                tool_fn = registry[name]
            except KeyError:
                result = {"error": f"no such tool: {name}"}
            else:
                try:
                    result = tool_fn(**args)
                except SourceEditRejected as exc:
                    result = {"error": str(exc)}
                except Exception as exc:
                    # Any other tool-execution failure (bad args, a path
                    # the model hallucinated that doesn't exist, ...) is a
                    # recoverable error the model should see and adapt to,
                    # not a reason to crash the whole fix loop. Only
                    # SourceEditRejected is a hard stop by design (the
                    # write guard); everything else gets reported back.
                    result = {"error": f"{type(exc).__name__}: {exc}"}
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id", name),
                    "content": json.dumps(result, default=str),
                }
            )

    return StageResult(
        "(stopped: exceeded tool-call round trip limit for this stage)", calls_made, time.perf_counter() - started
    )


def run_fix_loop(
    repo_path: str,
    *,
    gate_threshold: float = 80.0,
    publish: bool = False,
    provider: str | None = None,
    on_event: Callable[[str, dict], None] | None = None,
    model: ChatProvider | None = None,
    mutation_workers: int = 1,
) -> FixResult:
    """
    Run the full AI fix loop against repo_path.

    1. Measure a real baseline (coverage, gaps, mutation, risk).
    2. Prioritize up to MAX_FILES_PER_RUN files by risk score.
    3. Per file: the AI provider reads the source and writes a killing test
       via write_test_file (hard-guarded to tests/ only).
    4. A second call critiques the new test.
    5. Re-measure for real (deterministic, no LLM involved) and gate.
    6. If publish=True and the gate passes, commit and open a PR.
    7. Write an evidence report to watson-evidence/.

    provider: forwarded to ai_providers.get_provider() (None reads
    REPOGUARD_AI_PROVIDER, defaulting to "vertex").

    on_event: optional progress callback, called as on_event(type, data) at
    each stage boundary (web/fix_job.py streams these to the browser). It
    only reports what already happened; it never changes what the loop does.

    model: an already-built ChatProvider to use instead of get_provider()
    (not exposed on the CLI) -- lets a credential-free scripted provider
    (repoguard_engine/testing/scripted_provider.py) drive the real loop.

    mutation_workers: parallel mutant workers for both measurements (same
    numbers, less wall time).

    Raises AIProviderError immediately if the selected provider's
    credentials aren't set -- checked before the (multi-minute) mutation
    baseline runs, not after, so a missing-credentials failure is instant
    rather than waiting on a measurement that was going to be thrown away
    anyway.
    """
    emit = on_event or (lambda _type, _data: None)
    if model is None:
        model = get_provider(provider=provider)
    loop_started = time.perf_counter()
    timings: list[dict] = []

    repo = str(Path(repo_path).resolve())
    emit("baseline_start", {})
    started = time.perf_counter()
    baseline = run_pipeline(
        repo, include_mutation=True, include_endpoints=True, gate_threshold=gate_threshold,
        mutation_workers=mutation_workers,
    )
    timings.append({"stage": "baseline", "wall_s": time.perf_counter() - started})
    result = FixResult(repo_path=repo, baseline=baseline.dashboard, timings=timings)
    files = _priority_files(baseline.risk)
    emit("baseline_done", {"dashboard": baseline.dashboard, "files": files})

    for file_rel in files:
        result.files_attempted.append(file_rel)
        emit("writer_start", {"file": file_rel})

        writer_prompt = (
            f"File: {file_rel}\n"
            f"Coverage gaps (missing lines): {baseline.gap.missing_lines_by_file.get(file_rel, []) if baseline.gap else []}\n"
            f"Surviving mutants in this file:\n{describe_survivors(baseline.mutation, file_rel)}\n\n"
            "Read this file, then write one pytest test file under tests/ "
            "that kills as many of the surviving mutants as possible."
        )
        stage = _run_chat_stage(model, TEST_WRITER_PROMPT, writer_prompt, repo)
        timings.append({"stage": "writer", "file": file_rel, "wall_s": stage.wall_s})

        emit("critic_start", {"file": file_rel})
        critic_prompt = f"Review whatever test file(s) were just written for {file_rel}."
        stage = _run_chat_stage(model, CRITIC_PROMPT, critic_prompt, repo)
        timings.append({"stage": "critic", "file": file_rel, "wall_s": stage.wall_s})
        result.critic_notes.append(f"{file_rel}: {stage.content}")

    emit("remeasure_start", {})
    started = time.perf_counter()
    after = run_pipeline(
        repo, include_mutation=True, include_endpoints=True, gate_threshold=gate_threshold,
        mutation_workers=mutation_workers,
    )
    timings.append({"stage": "remeasure", "wall_s": time.perf_counter() - started})
    result.after = after.dashboard
    emit("remeasure_done", {"dashboard": after.dashboard, "passed_gate": after.passed_gate})

    if publish and after.passed_gate:
        _publish(repo)
        result.published = True

    if baseline.run_id and after.run_id and after.record:
        result.fix_session_id = _store_fix_session(after.record["project"], baseline.run_id, after.run_id, model, provider)

    result.wall_s = time.perf_counter() - loop_started
    result.evidence_path = _write_evidence(repo, result)
    return result


def _store_fix_session(project: str, before_run_id: str, after_run_id: str, model, provider: str | None) -> str:
    """Link the two stored runs; the effect itself is a view (v_fix_effect)."""
    from ..ai_providers import resolve_provider_name
    from ..store import database_url
    from ..store.db import get_engine
    from ..store.repository import save_fix_session

    return save_fix_session(
        get_engine(database_url()),
        project=project,
        before_run_id=before_run_id,
        after_run_id=after_run_id,
        provider=getattr(model, "name", None) or resolve_provider_name(provider),
        model_id=getattr(model, "model_id", None),
    )


def _publish(repo_path: str) -> None:
    """Branch, commit tests/ only, push, open a PR. Bare git/gh, like a human
    would run them -- same intentional exception as verify.py's phase0 check."""
    branch = f"fix/ai-{datetime.now(timezone.utc):%Y%m%d%H%M%S}"
    steps = [
        ["git", "checkout", "-b", branch],
        ["git", "add", "tests"],
        ["git", "commit", "-m", "test: AI fix loop"],
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
        f"# AI fix loop -- {datetime.now(timezone.utc).isoformat()}\n\n"
        f"Repo: {result.repo_path}\n\n"
        f"Files attempted: {', '.join(result.files_attempted) or '(none)'}\n\n"
        f"Wall time: {result.wall_s:.1f} s\n\n"
        "## Stage timings\n" + "".join(
            f"- {t['stage']}{' ' + t['file'] if 'file' in t else ''}: {t['wall_s']:.1f} s\n" for t in result.timings
        ) + "\n"
        f"## Before\n```json\n{json.dumps(result.baseline, indent=2)}\n```\n\n"
        f"## After\n```json\n{json.dumps(result.after, indent=2)}\n```\n\n"
        "## Critic notes\n" + "\n\n".join(result.critic_notes),
        encoding="utf-8",
    )
    return str(path)
