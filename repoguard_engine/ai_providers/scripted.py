from __future__ import annotations

from .base import ChatProvider


class ScriptedProvider(ChatProvider):
    """A ChatProvider that replays a fixed list of assistant turns (tool
    calls and final text). For verify.py and eval only: it is NOT reachable
    from get_provider() or REPOGUARD_AI_PROVIDER."""

    def __init__(self, turns: list[dict]):
        self.turns = turns
        self.cursor = 0

    def chat(self, messages: list[dict], tools: list[dict] | None = None, **kw) -> dict:
        if self.cursor >= len(self.turns):
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "(scripted provider ran out of turns)"
                        }
                    }
                ]
            }
        turn = self.turns[self.cursor]
        self.cursor += 1
        return {"choices": [{"message": turn}]}
