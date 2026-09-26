"""
Narrative summary: turns an already-measured dashboard dict into human-
readable prose via whichever AI provider REPOGUARD_AI_PROVIDER selects
(Vertex AI by default, or watsonx.ai) -- see docs/MULTICLOUD_AI.md. This
module never measures anything itself and never invents a number — every
figure it can mention has to already exist in the dict it's given. See
AGENTS.md Section 4: "the AI decides, the engine measures."

Requires credentials for the selected provider (docs/WATSONX_SETUP.md or
docs/VERTEX_SETUP.md). Degrades gracefully (ok=False, a real error message)
rather than raising or fabricating text when the SDK isn't installed or
credentials are missing — same pattern as visual.py's Playwright/axe checks.
"""

from __future__ import annotations

from dataclasses import dataclass

from .ai_providers import get_provider, resolve_provider_name

_TIMEOUT_SECONDS = 30
_MAX_NEW_TOKENS = 300


@dataclass
class NarrativeResult:
    ok: bool
    text: str = ""
    error: str = ""
    provider: str = ""


def _build_prompt(dashboard: dict) -> str:
    """Render *dashboard* (the exact dict from core.build_dashboard_data)
    into a prompt that only ever asks the model to explain given numbers,
    never to produce or adjust one."""
    coverage = dashboard.get("coverage") or {}
    mutation = dashboard.get("mutation")
    gaps = dashboard.get("gaps") or {}
    risk = dashboard.get("risk") or []

    lines = [
        "You are writing a short, plain-English summary of pre-computed "
        "software test-quality metrics for a report. Use ONLY the numbers "
        "given below. Do not calculate, estimate, round differently, or "
        "invent any number, file name, or metric not listed here. If a "
        "value is missing, say it wasn't measured — do not guess it.",
        "",
        f"Coverage: {coverage.get('percent')}% "
        f"({coverage.get('covered_lines')} of {coverage.get('total_lines')} lines)",
        f"Files with coverage gaps: {len(gaps.get('uncovered_files', []))}",
    ]
    if mutation:
        lines.append(
            f"Mutation score: {mutation.get('score')}% "
            f"({mutation.get('killed')} of {mutation.get('total')} mutants killed, "
            f"{mutation.get('survived')} survived)"
        )
    else:
        lines.append("Mutation score: not measured in this run")
    if risk:
        top = ", ".join(f"{r.get('file')} ({r.get('score')})" for r in risk[:3])
        lines.append(f"Top risk files: {top}")

    lines.append(
        "\nWrite 2-4 sentences: what these numbers mean for someone deciding "
        "whether this code is safe to ship, and which file to look at first."
    )
    return "\n".join(lines)


def generate_summary(
    dashboard: dict,
    *,
    provider: str | None = None,
    model_id: str | None = None,
) -> NarrativeResult:
    """
    Ask the configured AI provider for a plain-English summary of an
    already-measured *dashboard* dict (the exact shape
    core.build_dashboard_data returns). Never computes or alters a metric —
    advisory text only.

    provider/model_id are forwarded to ai_providers.get_provider(); None
    reads REPOGUARD_AI_PROVIDER, defaulting to "vertex".
    """
    resolved_provider = resolve_provider_name(provider)
    prompt = _build_prompt(dashboard)

    try:
        chat = get_provider(provider=provider, model_id=model_id)
        response = chat.chat(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=_MAX_NEW_TOKENS,
            timeout_ms=_TIMEOUT_SECONDS * 1000,
        )
        text = response["choices"][0]["message"]["content"]
        return NarrativeResult(ok=True, text=text.strip(), provider=resolved_provider)
    except Exception as exc:
        # Any SDK/auth/network failure -- never fabricate a summary.
        return NarrativeResult(ok=False, error=str(exc), provider=resolved_provider)
