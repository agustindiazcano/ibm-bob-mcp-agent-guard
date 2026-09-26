"""Credential-free test doubles for the AI fix loop (and, later, the Phase 18
swarm). Nothing in the CLI, MCP server or web app imports this package."""

from .scripted_provider import ScriptedCall, ScriptedProvider, approving_critic, reference_writer

__all__ = ["ScriptedCall", "ScriptedProvider", "approving_critic", "reference_writer"]
