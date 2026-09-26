"""ChatProvider protocol: the one interface both narrative.py's advisory
summary and watson_agent/orchestrator.py's tool-calling fix loop call
through, so neither has to know which cloud is actually configured.

Response shape is the OpenAI-compatible chat/tool-calling convention
(`{"choices": [{"message": {...}}]}`) already used by
`watson_agent/tools.py`'s TOOL_SCHEMAS -- every provider implementation
translates its own SDK's real call/response into this shape, not the other
way around.
"""

from __future__ import annotations

from typing import Protocol


class AIProviderError(RuntimeError):
    """Credentials missing/invalid, or the SDK for the selected provider
    isn't installed. Callers should catch this generically; each provider
    module may still raise a named subclass for provider-specific detail."""


class ChatProvider(Protocol):
    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        *,
        max_tokens: int | None = None,
        timeout_ms: int | None = None,
    ) -> dict:
        """Returns a dict shaped like {"choices": [{"message": {...}}]}."""
        ...
