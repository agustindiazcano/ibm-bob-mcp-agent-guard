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
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from .._common import write_out
from ..ai_providers import ChatProvider, get_provider
from ..pipeline import run_pipeline
from .acceptance import (
    accept_file,
    changed_test_files,
    collect_test_ids,
    quarantine,
    snapshot_tests,
)
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
    # One row per AI stage: {"file", "stage", "wall_s", "llm_calls", "tool_calls"}.
    stages: list[dict] = field(default_factory=list)
    # Wall seconds per phase: "baseline", "ai", "remeasure", "total". Phase 18's
    # H1 (swarm vs sequential speed) needs these; Phase 11's run recorded none.
    wall_s: dict[str, float] = field(default_factory=dict)
    
    status: Literal["accepted", "partial", "rejected", "error"] = "error"
    integrity: dict = field(default_factory=dict)
    acceptance: list[dict] = field(default_factory=list)


@dataclass
class StageResult:
    """What one chat-with-tools stage did: the model's final text, the tools it
    called in order, how many chat() round trips it took, and its wall time."""

    content: str
    tool_calls: list[dict] = field(default_factory=list)
    llm_calls: int = 0
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
    stage_name: str,
    file_rel: str,
    model: ChatProvider,
    system_prompt: str,
    user_prompt: str,
    repo_path: str,
    *,
    schemas: list[dict] = TOOL_SCHEMAS,
    registry: dict[str, Callable[..., dict]] = TOOL_REGISTRY,
) -> StageResult:
    """One chat-with-tools stage against the configured AI provider, looping
    on tool calls until the model returns plain content or the round-trip
    cap is hit.

    schemas/registry default to the full fix-loop toolset; a caller can pass
    a narrower pair (e.g. a critic with no write tool). A tool the model
    calls that isn't in `registry` is reported back as an error, never run."""
    started = time.perf_counter()
    stage = StageResult(content="")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for _ in range(MAX_TOOL_ROUNDS_PER_STAGE):
        response = model.chat(messages=messages, tools=schemas)
        stage.llm_calls += 1
        message = response["choices"][0]["message"]
        messages.append(message)
        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            stage.content = message.get("content", "") or ""
            stage.wall_s = time.perf_counter() - started
            return stage

        for call in tool_calls:
            tool_start = time.perf_counter()
            name = call["function"]["name"]
            try:
                args = json.loads(call["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {}
            
            target_path = args.get("file_path") or args.get("test_path") or None
            
            args["repo_path"] = repo_path
            outcome_str = "ok"
            try:
                tool_fn = registry[name]
            except KeyError:
                result = {"error": f"no such tool: {name}"}
                outcome_str = "error"
            else:
                try:
                    result = tool_fn(**args)
                except SourceEditRejected as exc:
                    result = {"error": str(exc)}
                    outcome_str = "rejected:SourceEditRejected"
                except Exception as exc:
                    # Any other tool-execution failure (bad args, a path
                    # the model hallucinated that doesn't exist, ...) is a
                    # recoverable error the model should see and adapt to,
                    # not a reason to crash the whole fix loop. Only
                    # SourceEditRejected is a hard stop by design (the
                    # write guard); everything else gets reported back.
                    result = {"error": f"{type(exc).__name__}: {exc}"}
                    outcome_str = "error"
            
            stage.tool_calls.append({
                "stage": stage_name,
                "file": file_rel,
                "tool": name,
                "arguments": args,
                "target": target_path,
                "outcome": outcome_str,
                "ms": int((time.perf_counter() - tool_start) * 1000)
            })
            
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id", name),
                    "content": json.dumps(result, default=str),
                }
            )

    stage.content = "(stopped: exceeded tool-call round trip limit for this stage)"
    stage.wall_s = time.perf_counter() - started
    return stage


def run_fix_loop(
    repo_path: str,
    *,
    gate_threshold: float = 80.0,
    publish: bool = False,
    provider: str | None = None,
    model_id: str | None = None,
    on_event: Callable[[str, dict], None] | None = None,
    model: ChatProvider | None = None,
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

    model_id: forwarded to ai_providers.get_provider() alongside provider
    (None uses that provider module's own default). Ignored when model is set.

    on_event: optional progress callback, called as on_event(type, data) at
    each stage boundary (web/fix_job.py streams these to the browser). It
    only reports what already happened; it never changes what the loop does.

    model: an already-built ChatProvider to use instead of calling
    get_provider(); `provider` is ignored when it's set. Not exposed on the
    CLI -- it exists so tests can inject a scripted, credential-free
    provider (repoguard_engine/testing/scripted_provider.py).

    Raises AIProviderError immediately if the selected provider's
    credentials aren't set -- checked before the (multi-minute) mutation
    baseline runs, not after, so a missing-credentials failure is instant
    rather than waiting on a measurement that was going to be thrown away
    anyway.
    """
    started = time.perf_counter()
    emit = on_event or (lambda _type, _data: None)
    if model is None:
        model = get_provider(provider=provider, model_id=model_id)

    repo = str(Path(repo_path).resolve())
    emit("baseline_start", {})
    phase_started = time.perf_counter()
    # persist=False: a before/after pair only means something stored as a linked
    # fix session (DATA_PLATFORM.md §13 A3.4), not as two unrelated runs -- and
    # web Autofix runs on a temp copy whose directory name isn't a project.
    baseline = run_pipeline(
        repo, include_mutation=True, include_endpoints=True, gate_threshold=gate_threshold, persist=False,
    )
    result = FixResult(repo_path=repo, baseline=baseline.dashboard)
    result.wall_s["baseline"] = time.perf_counter() - phase_started
    files = _priority_files(baseline.risk)
    emit("baseline_done", {"dashboard": baseline.dashboard, "files": files})

    before = snapshot_tests(Path(repo))
    ids_before = collect_test_ids(Path(repo))
    accepted_files = set()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    
    result.integrity = {
        "policy": 0, "quarantined": 0, "canary": 0,
        "flaky": 0, "preserved_ids_restored": 0,
        "survivor_regressions": 0,
    }

    phase_started = time.perf_counter()
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
        writer = _run_chat_stage("writer", file_rel, model, TEST_WRITER_PROMPT, writer_prompt, repo)
        result.stages.append(_stage_row(file_rel, "writer", writer))

        emit("critic_start", {"file": file_rel})
        critic_prompt = f"Review whatever test file(s) were just written for {file_rel}."
        critic = _run_chat_stage("critic", file_rel, model, CRITIC_PROMPT, critic_prompt, repo)
        result.stages.append(_stage_row(file_rel, "critic", critic))
        result.critic_notes.append(f"{file_rel}: {critic.content}")
        
        # acceptance
        for test_file in changed_test_files(before, Path(repo)):
            if test_file not in accepted_files:
                acc = accept_file(Path(repo), test_file)
                result.acceptance.append({"file": test_file, "accepted": acc.accepted, "reasons": acc.reasons})
                if acc.accepted:
                    accepted_files.add(test_file)
                else:
                    orig = before.get(test_file)
                    quarantine(Path(repo), test_file, acc, run_id, orig)
                    result.integrity["quarantined"] += 1
                    for r in acc.reasons:
                        if r.startswith("Policy"): result.integrity["policy"] += 1
                        elif r.startswith("Canary"): result.integrity["canary"] += 1
                        elif r.startswith("Repetition"): result.integrity["flaky"] += 1
                emit("acceptance", {"file": test_file, "accepted": acc.accepted, "reasons": acc.reasons})
                
    # Preservation check
    ids_after = collect_test_ids(Path(repo))
    if not ids_before.issubset(ids_after):
        missing = ids_before - ids_after
        for test_file in list(accepted_files) + changed_test_files(before, Path(repo)):
            if Path(test_file).exists():
                orig = before.get(test_file)
                acc = accept_file(Path(repo), test_file) # Just a dummy to quarantine
                acc.accepted = False
                acc.reasons = ["Preservation: missing original test IDs"]
                quarantine(Path(repo), test_file, acc, run_id, orig)
                result.integrity["quarantined"] += 1
                result.integrity["preserved_ids_restored"] += 1
                if test_file in accepted_files:
                    accepted_files.remove(test_file)
                emit("acceptance", {"file": test_file, "accepted": False, "reasons": acc.reasons})
                
    # Whole-suite check
    acc_suite = accept_file(Path(repo), "tests")
    if not acc_suite.accepted:
        new_files = [f for f in accepted_files if f not in before]
        # Drop one by one (bisection)
        for offender in new_files:
            orig = before.get(offender)
            tgt = Path(repo) / offender
            tgt.unlink(missing_ok=True)
            acc_check = accept_file(Path(repo), "tests")
            if acc_check.accepted:
                # Found the offender
                acc = accept_file(Path(repo), offender) # Just for the object
                acc.accepted = False
                acc.reasons = ["Whole-suite: fails when run together with others"]
                quarantine(Path(repo), offender, acc, run_id, orig)
                accepted_files.remove(offender)
                emit("acceptance", {"file": offender, "accepted": False, "reasons": acc.reasons})
                break
            # Restore if it didn't help
            if orig is not None:
                tgt.write_bytes(orig)
            elif tgt.exists():
                tgt.unlink()

    result.wall_s["ai"] = time.perf_counter() - phase_started

    emit("remeasure_start", {})
    phase_started = time.perf_counter()
    try:
        if not accepted_files:
            class _DummyPipelineResult:
                def __init__(self, d):
                    self.dashboard = d
                    self.passed_gate = False
                    self.mutation = type('Mutation', (), {'surviving_mutant_ids': d.get("mutation", {}).get("surviving_mutant_ids", [])})() if d.get("mutation") else None
            after = _DummyPipelineResult(baseline.dashboard)
        else:
            after = run_pipeline(
                repo, include_mutation=True, include_endpoints=True, gate_threshold=gate_threshold, persist=False,
            )
        result.after = after.dashboard
        result.wall_s["remeasure"] = time.perf_counter() - phase_started
        emit("remeasure_done", {"dashboard": after.dashboard, "passed_gate": after.passed_gate})
        
        k_a = result.after["mutation"]["killed"] if result.after and result.after.get("mutation") else 0
        k_b = result.baseline["mutation"]["killed"] if result.baseline and result.baseline.get("mutation") else 0
        surv_before = set(baseline.mutation.surviving_mutant_ids) if baseline.mutation else set()
        surv_after = set(after.mutation.surviving_mutant_ids) if after.mutation else set()
        
        result.integrity["survivor_regressions"] = len(surv_after - surv_before)
        
        if result.integrity["survivor_regressions"] > 0 or not accepted_files or k_a <= k_b:
            result.status = "rejected"
        elif result.integrity["quarantined"] == 0:
            result.status = "accepted"
        else:
            result.status = "partial"
            
        if publish and result.status == "accepted" and after.passed_gate:
            _publish(repo)
            result.published = True
            
    except RuntimeError as exc:
        result.status = "rejected"
        result.critic_notes.append(f"RuntimeError in re-measure: {exc}")
        result.wall_s["remeasure"] = time.perf_counter() - phase_started
    except Exception as exc:
        result.status = "error"
        result.critic_notes.append(f"Error in re-measure: {exc}")
        result.wall_s["remeasure"] = time.perf_counter() - phase_started
    finally:
        result.wall_s["total"] = time.perf_counter() - started
        result.evidence_path = _write_evidence(repo, result)
        _write_fix_run(repo, result, model)

    return result


def _stage_row(file_rel: str, stage: str, outcome: StageResult) -> dict:
    return {
        "file": file_rel,
        "stage": stage,
        "wall_s": round(outcome.wall_s, 3),
        "llm_calls": outcome.llm_calls,
        "tool_calls": outcome.tool_calls,
    }


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
        f"## Before\n```json\n{json.dumps(result.baseline, indent=2)}\n```\n\n"
        f"## After\n```json\n{json.dumps(result.after, indent=2)}\n```\n\n"
        f"{_timing_section(result)}\n\n"
        "## Critic notes\n" + "\n\n".join(result.critic_notes),
        encoding="utf-8",
    )
    return str(path)


def _timing_section(result: FixResult) -> str:
    """Wall time per phase and per AI stage, as measured by run_fix_loop."""
    lines = ["## Timing", "", "| Phase | Wall s |", "|---|---|"]
    lines += [f"| {phase} | {seconds:.1f} |" for phase, seconds in result.wall_s.items()]
    lines += ["", "| File | Stage | Wall s | LLM calls | Tools called |", "|---|---|---|---|---|"]
    lines += [
        f"| {row['file']} | {row['stage']} | {row['wall_s']:.1f} | {row['llm_calls']} | "
        f"{', '.join(tc['tool'] for tc in row['tool_calls']) or '(none)'} |"
        for row in result.stages
    ]
    return "\n".join(lines)


def _write_fix_run(repo_path: str, result: FixResult, model: ChatProvider) -> None:
    """Structured run record (O1, docs/EVAL_GUARDRAILS_IMPLEMENTATION.md
    Section 9) -- everything eval/benchmark tooling needs to score this run
    without re-parsing watson-evidence/'s prose report."""
    all_tool_calls = [tc for stage in result.stages for tc in stage["tool_calls"]]
    record = {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
        "repo_path": result.repo_path,
        "provider": type(model).__name__,
        # Best-effort: not every ChatProvider implementation exposes this,
        # and the Protocol doesn't require it -- never guessed.
        "model_id": getattr(model, "model_id", None) or getattr(model, "_model_id", None),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "wall_s": result.wall_s,
        "llm_calls": sum(row["llm_calls"] for row in result.stages),
        "usage": None,
        "status": result.status,
        "files_attempted": result.files_attempted,
        "integrity": result.integrity,
        "acceptance": result.acceptance,
        "tool_calls": all_tool_calls,
        "before": (result.baseline or {}).get("mutation"),
        "after": (result.after or {}).get("mutation"),
        "published": result.published,
        "evidence_path": result.evidence_path,
    }
    write_out(Path(repo_path), "fix_run", record)
