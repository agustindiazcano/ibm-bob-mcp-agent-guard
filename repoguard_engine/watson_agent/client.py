"""watsonx.ai chat client for the fix-loop orchestrator (tool-calling).

Separate from narrative.py's plain generate_text() call: the fix loop needs a
tool-calling-capable chat model to drive the test-writer/critic stages, not a
one-shot text completion. Reuses the same env vars and the same fail-loud
stance as narrative.py -- a missing credential is a clear error, never a
silent no-op (AGENTS.md Section 9's "never silently fabricate a result").

Verified against the actually-installed ibm-watsonx-ai==1.7.2 via
inspect.signature()/help(): ModelInference.__init__ takes model_id,
credentials, project_id as used below; ModelInference.chat(messages, tools=)
returns a dict shaped like response["choices"][0]["message"], matching the
OpenAI-compatible tool-calling convention this module assumes. Not verified:
an actual live tool-calling round trip (needs a real IBM Cloud account) --
same gap already documented in docs/WATSONX_SETUP.md for narrative.py.
"""

from __future__ import annotations

import os

DEFAULT_MODEL_ID = "meta-llama/llama-3-3-70b-instruct"
DEFAULT_URL = "https://us-south.ml.cloud.ibm.com"


class WatsonxCredentialsError(RuntimeError):
    """WATSONX_APIKEY / WATSONX_PROJECT_ID are missing, or the SDK isn't installed."""


def get_chat_model(*, model_id: str = DEFAULT_MODEL_ID):
    """
    Build an ibm_watsonx_ai ModelInference configured for chat + tool calling.

    Uses the same WATSONX_APIKEY / WATSONX_PROJECT_ID / WATSONX_URL env vars
    as narrative.py (docs/WATSONX_SETUP.md) -- one credential setup covers
    both the narrative summary and the fix-loop orchestrator.

    Raises WatsonxCredentialsError immediately if credentials are missing or
    the SDK isn't installed -- the fix loop must fail loudly here, not run
    with a model that silently can't be reached.
    """
    api_key = os.environ.get("WATSONX_APIKEY")
    project_id = os.environ.get("WATSONX_PROJECT_ID")
    url = os.environ.get("WATSONX_URL", DEFAULT_URL)

    if not api_key or not project_id:
        raise WatsonxCredentialsError(
            "WATSONX_APIKEY and WATSONX_PROJECT_ID must be set -- see docs/WATSONX_SETUP.md"
        )

    try:
        from ibm_watsonx_ai import Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference
    except ImportError as exc:
        raise WatsonxCredentialsError(
            "ibm-watsonx-ai is not installed (pip install 'repoguard[ai]')"
        ) from exc

    return ModelInference(
        model_id=model_id,
        credentials=Credentials(url=url, api_key=api_key),
        project_id=project_id,
    )
