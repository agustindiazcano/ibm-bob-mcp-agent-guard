"""The lane Critic (Phase 18 S5, docs/MULTI_AGENT_SWARM.md Section 4.4).

Read-only: it gets critic_toolset() (read_source_file + run_tests, no write
tool) and must answer with one JSON verdict. The verdict is advisory -- it
decides whether the writer gets another round, never whether the lane is
accepted; acceptance always comes from the Verifier's own measurement.

A reply that isn't a valid verdict gets exactly one "JSON only" re-ask; if
that fails too, the verdict is recorded as UNPARSEABLE and the lane doesn't
revise on it (a model that can't produce the contract shouldn't drive
another paid round).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..ai_providers import ChatProvider
from ..watson_agent.orchestrator import _run_chat_stage
from ..watson_agent.prompts import SWARM_CRITIC_PROMPT
from .guard import critic_toolset

VERDICTS = ("APPROVED", "NEEDS_WORK", "BLOCKED")
UNPARSEABLE = "UNPARSEABLE"

_REASK = (
    "Your last reply was not a valid verdict. Reply with ONE JSON object and nothing else, "
    'e.g. {"verdict": "NEEDS_WORK", "weaknesses": [{"test": "...", "issue": "...", "mutant_ids": []}], '
    '"blocker": null}. Your last reply was:\n'
)


@dataclass
class CriticVerdict:
    verdict: str  # one of VERDICTS, or UNPARSEABLE
    weaknesses: list[dict] = field(default_factory=list)
    blocker: str | None = None
    raw: list[str] = field(default_factory=list)  # every reply, in order
    llm_calls: int = 0
    tool_calls: list[dict] = field(default_factory=list)
    wall_s: float = 0.0


def parse_verdict(text: str) -> dict | None:
    """The first JSON object in `text` whose "verdict" is one of VERDICTS,
    normalized to {"verdict", "weaknesses", "blocker"}; None if there isn't one.
    Tolerates prose or a ```json fence around the object."""
    decoder = json.JSONDecoder()
    start = text.find("{")
    while start != -1:
        try:
            obj, _end = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            start = text.find("{", start + 1)
            continue
        if isinstance(obj, dict) and obj.get("verdict") in VERDICTS:
            weaknesses = obj.get("weaknesses") or []
            if not isinstance(weaknesses, list):
                weaknesses = []
            blocker = obj.get("blocker")
            return {
                "verdict": obj["verdict"],
                "weaknesses": [w for w in weaknesses if isinstance(w, dict)],
                "blocker": blocker if isinstance(blocker, str) else None,
            }
        start = text.find("{", start + 1)
    return None


def critic_prompt(module: str, owned: str, still_alive: list[dict]) -> str:
    alive = "\n".join(
        f"  - {r['fingerprint']}: line {r['lineno']} in {r['function']}: {r['description']}  | {r['original_line']}"
        for r in still_alive
    )
    return (
        f"Source file: {module}\n"
        f"Lane test file: {owned}\n"
        f"Mutants still alive after this round (fingerprint: what changed):\n{alive or '  (none)'}\n\n"
        f"Run run_tests on {owned}, read {module}, then reply with the JSON verdict."
    )


def run_critic(sandbox: str | Path, module: str, owned: str, provider: ChatProvider, still_alive: list[dict]) -> CriticVerdict:
    """One critic stage (plus at most one JSON-only re-ask) against the lane's
    sandbox. Never writes a file: the toolset has no write tool, and a call to
    one is answered with "no such tool" by _run_chat_stage."""
    schemas, registry = critic_toolset()
    result = CriticVerdict(verdict=UNPARSEABLE)
    prompt = critic_prompt(module, owned, still_alive)
    for attempt in range(2):
        stage = _run_chat_stage(
            "critic", module, provider, SWARM_CRITIC_PROMPT, prompt, str(sandbox), schemas=schemas, registry=registry
        )
        result.raw.append(stage.content)
        result.llm_calls += stage.llm_calls
        result.tool_calls += stage.tool_calls
        result.wall_s += stage.wall_s
        parsed = parse_verdict(stage.content)
        if parsed is not None:
            result.verdict = parsed["verdict"]
            result.weaknesses = parsed["weaknesses"]
            result.blocker = parsed["blocker"]
            return result
        if attempt == 0:
            prompt = critic_prompt(module, owned, still_alive) + "\n\n" + _REASK + stage.content[:2000]
    return result
