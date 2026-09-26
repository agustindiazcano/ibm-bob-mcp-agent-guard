"""Provider-agnostic AI layer: narrative.py and watson_agent/orchestrator.py
call get_provider() instead of importing a specific cloud SDK. See
docs/MULTICLOUD_AI.md for the design and docs/WATSONX_SETUP.md /
docs/VERTEX_SETUP.md for credential setup.

REPOGUARD_AI_PROVIDER selects the backend ("watsonx", the default, or
"vertex"); get_provider(provider=...) overrides it per call (used by
`repoguard fix --provider` / `repoguard analyze --summarize --provider`).
Imports are lazy per branch so a watsonx-only install never touches Google
packages and vice versa.
"""

from __future__ import annotations

import os

from .base import AIProviderError, ChatProvider

__all__ = ["AIProviderError", "ChatProvider", "get_provider"]


def get_provider(*, provider: str | None = None, model_id: str | None = None) -> ChatProvider:
    """
    Build a ChatProvider for the configured backend.

    provider: explicit override; if None, reads REPOGUARD_AI_PROVIDER,
    defaulting to "watsonx" -- unchanged default behavior for anyone not
    opting in.
    model_id: optional override passed straight to the selected provider's
    own factory; if None, that provider module's own DEFAULT_MODEL_ID is
    used (each provider keeps owning its own suited default).

    Raises AIProviderError immediately (fail loud, never a silent fallback
    to a different provider) if credentials are missing/invalid, the SDK
    isn't installed, or the provider name is unrecognized.
    """
    provider = provider or os.environ.get("REPOGUARD_AI_PROVIDER", "watsonx")

    if provider == "watsonx":
        from . import watsonx

        return watsonx.get_provider(model_id=model_id) if model_id else watsonx.get_provider()

    if provider == "vertex":
        from . import vertex

        return vertex.get_provider(model_id=model_id) if model_id else vertex.get_provider()

    raise AIProviderError(f"Unknown REPOGUARD_AI_PROVIDER: {provider!r} (expected 'watsonx' or 'vertex')")
