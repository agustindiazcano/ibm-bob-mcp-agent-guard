"""IBM watsonx.ai ChatProvider -- the alternative provider
(REPOGUARD_AI_PROVIDER=watsonx / --provider watsonx; the default is vertex). Replaces the former watson_agent/client.py; moved here
unchanged apart from wrapping ModelInference.chat() behind the normalized
ChatProvider.chat(messages, tools=, max_tokens=, timeout_ms=) signature so
narrative.py and the fix-loop orchestrator never import ibm_watsonx_ai
directly.

Verified against the actually-installed ibm-watsonx-ai==1.7.2 via
inspect.signature()/help():
- ModelInference.__init__ takes model_id, credentials, project_id as used
  below.
- ModelInference.chat(messages, params=None, tools=None, tool_choice=None,
  tool_choice_option=None, context=None, crypto=None) -> dict, returning a
  dict shaped like response["choices"][0]["message"] -- the OpenAI-compatible
  tool-calling convention this module (and watson_agent/tools.py) assumes.
- chat()'s params dict uses "max_tokens"/"time_limit" -- NOT "max_new_tokens"
  (that's generate_text()'s completion-API param name, a different call this
  module doesn't use).

Live-verified this session: a real tool-calling round trip against a real
IBM Cloud account (model mistralai/mistral-small-3-1-24b-instruct-2503) --
the call itself works, though that particular model didn't reliably invoke
tools (a model-choice quality issue, not a bug in this call shape).
"""

from __future__ import annotations

import os

from .base import AIProviderError

DEFAULT_MODEL_ID = "mistralai/mistral-small-3-1-24b-instruct-2503"
DEFAULT_URL = "https://us-south.ml.cloud.ibm.com"


class WatsonxCredentialsError(AIProviderError):
    """WATSONX_APIKEY / WATSONX_PROJECT_ID are missing, or the SDK isn't installed."""


class WatsonxChatProvider:
    name = "watsonx"

    def __init__(self, model, model_id: str | None = None) -> None:
        self._model = model
        self.model_id = model_id

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        *,
        max_tokens: int | None = None,
        timeout_ms: int | None = None,
    ) -> dict:
        params: dict = {}
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        if timeout_ms is not None:
            params["time_limit"] = timeout_ms
        return self._model.chat(messages=messages, tools=tools, params=params or None)


def get_provider(*, model_id: str = DEFAULT_MODEL_ID) -> WatsonxChatProvider:
    """
    Build a WatsonxChatProvider wrapping an ibm_watsonx_ai ModelInference
    configured for chat + tool calling.

    Uses WATSONX_APIKEY / WATSONX_PROJECT_ID / WATSONX_URL env vars
    (docs/WATSONX_SETUP.md) -- one credential setup covers both the
    narrative summary and the fix-loop orchestrator.

    Raises WatsonxCredentialsError immediately if credentials are missing or
    the SDK isn't installed -- callers must fail loudly here, never run with
    a model that silently can't be reached.
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

    model = ModelInference(
        model_id=model_id,
        credentials=Credentials(url=url, api_key=api_key),
        project_id=project_id,
    )
    return WatsonxChatProvider(model, model_id=model_id)
