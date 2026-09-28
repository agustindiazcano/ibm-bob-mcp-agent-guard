"""Per-role AI providers for the swarm (Phase 18 S9, folded into S5).

The writer and the critic can run on different providers -- an independent
critic is part of what H2 measures, not an assumption. Resolution per role:
REPOGUARD_WRITER_PROVIDER / REPOGUARD_CRITIC_PROVIDER, then the caller's
--provider, then REPOGUARD_AI_PROVIDER (ai_providers.resolve_provider_name).
model_id only applies to roles that resolve to the same provider as the
caller's own choice -- a Gemini model id is meaningless on watsonx.
"""

from __future__ import annotations

import os
from collections.abc import Callable

from ..ai_providers import ChatProvider, get_provider, resolve_provider_name

ROLES = ("writer", "critic")


def role_provider_name(role: str, provider: str | None = None) -> str:
    override = os.environ.get(f"REPOGUARD_{role.upper()}_PROVIDER")
    return resolve_provider_name(override or provider)


def role_provider_factory(provider: str | None = None, model_id: str | None = None) -> Callable[[str], ChatProvider]:
    """A provider_factory(role) for run_lanes. Builds one provider per role
    eagerly first, so missing credentials for either role fail in
    milliseconds -- before the multi-minute baseline (same rule as
    run_fix_loop) -- then hands each lane its own fresh instance."""
    main = resolve_provider_name(provider)

    def factory(role: str) -> ChatProvider:
        name = role_provider_name(role, provider)
        return get_provider(provider=name, model_id=model_id if name == main else None)

    for role in ROLES:
        factory(role)
    return factory
