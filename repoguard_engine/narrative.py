"""
Narrative summary: turns an already-measured dashboard dict into human-
readable prose via IBM watsonx.ai. This module never measures anything
itself and never invents a number — every figure it can mention has to
already exist in the dict it's given. See AGENTS.md Section 4: "the AI
decides, the engine measures."

Requires IBM Cloud credentials (WATSONX_APIKEY, WATSONX_PROJECT_ID, and
optionally WATSONX_URL) — see docs/WATSONX_SETUP.md for how to get them.
Degrades gracefully (ok=False, a real error message) rather than raising or
fabricating text when the SDK isn't installed or credentials are missing —
same pattern as visual.py's Playwright/axe checks.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_MODEL_ID = "ibm/granite-3-8b-instruct"
DEFAULT_URL = "https://us-south.ml.cloud.ibm.com"
_TIMEOUT_SECONDS = 30


@dataclass
class NarrativeResult:
    ok: bool
    text: str = ""
    error: str = ""


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
    api_key: str | None = None,
    project_id: str | None = None,
    url: str | None = None,
    model_id: str = DEFAULT_MODEL_ID,
) -> NarrativeResult:
    """
    Ask watsonx.ai for a plain-English summary of an already-measured
    *dashboard* dict (the exact shape core.build_dashboard_data returns).
    Never computes or alters a metric — advisory text only.
    """
    api_key = api_key or os.environ.get("WATSONX_APIKEY")
    project_id = project_id or os.environ.get("WATSONX_PROJECT_ID")
    url = url or os.environ.get("WATSONX_URL", DEFAULT_URL)

    if not api_key or not project_id:
        return NarrativeResult(
            ok=False,
            error="WATSONX_APIKEY and WATSONX_PROJECT_ID must be set — see docs/WATSONX_SETUP.md",
        )

    try:
        from ibm_watsonx_ai import Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference
    except ImportError:
        return NarrativeResult(
            ok=False,
            error="ibm-watsonx-ai is not installed (pip install 'repoguard[ai]')",
        )

    prompt = _build_prompt(dashboard)

    try:
        model = ModelInference(
            model_id=model_id,
            credentials=Credentials(url=url, api_key=api_key),
            project_id=project_id,
        )
        response = model.generate_text(
            prompt=prompt,
            params={"time_limit": _TIMEOUT_SECONDS * 1000},
        )
        text = response if isinstance(response, str) else str(response)
        return NarrativeResult(ok=True, text=text.strip())
    except Exception as exc:
        # Any SDK/auth/network failure -- never fabricate a summary.
        return NarrativeResult(ok=False, error=str(exc))
