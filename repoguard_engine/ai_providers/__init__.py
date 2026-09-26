"""Provider-agnostic AI layer: narrative.py and watson_agent/orchestrator.py
call get_provider() instead of importing a specific cloud SDK. See
docs/MULTICLOUD_AI.md for the design and docs/WATSONX_SETUP.md /
docs/VERTEX_SETUP.md for credential setup.

REPOGUARD_AI_PROVIDER selects the backend ("vertex", the default, or
"watsonx"); get_provider(provider=...) overrides it per call (used by
`repoguard fix --provider` / `repoguard analyze --summarize --provider`).
Imports are lazy per branch so a watsonx-only install never touches Google
packages and vice versa.
"""

from __future__ import annotations

import os

from .base import AIProviderError, ChatProvider

__all__ = ["AIProviderError", "ChatProvider", "DEFAULT_PROVIDER", "get_provider", "resolve_provider_name"]

# Vertex AI (Gemini 3) is the primary provider: it's the one the deployed
# service runs and the one that reached 89.87% on demo-repo in Phase 11.
# watsonx.ai stays available via REPOGUARD_AI_PROVIDER=watsonx / --provider.
DEFAULT_PROVIDER = "vertex"


def resolve_provider_name(provider: str | None = None) -> str:
    """The provider name a call will actually use: the explicit override,
    else REPOGUARD_AI_PROVIDER, else DEFAULT_PROVIDER."""
    return provider or os.environ.get("REPOGUARD_AI_PROVIDER") or DEFAULT_PROVIDER


def get_provider(*, provider: str | None = None, model_id: str | None = None) -> ChatProvider:
    """
    Build a ChatProvider for the configured backend.

    provider: explicit override; if None, reads REPOGUARD_AI_PROVIDER,
    defaulting to DEFAULT_PROVIDER ("vertex").
    model_id: optional override passed straight to the selected provider's
    own factory; if None, that provider module's own DEFAULT_MODEL_ID is
    used (each provider keeps owning its own suited default).

    Raises AIProviderError immediately (fail loud, never a silent fallback
    to a different provider) if credentials are missing/invalid, the SDK
    isn't installed, or the provider name is unrecognized.
    """
    provider = resolve_provider_name(provider)

    if provider == "watsonx":
        from . import watsonx

        return watsonx.get_provider(model_id=model_id) if model_id else watsonx.get_provider()

    if provider == "vertex":
        from . import vertex

        return vertex.get_provider(model_id=model_id) if model_id else vertex.get_provider()

    raise AIProviderError(f"Unknown REPOGUARD_AI_PROVIDER: {provider!r} (expected 'watsonx' or 'vertex')")
