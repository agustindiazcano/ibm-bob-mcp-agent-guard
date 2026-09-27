from __future__ import annotations

class ScriptedProvider:
    """A ChatProvider that replays a fixed list of assistant turns (tool
    calls and final text). For verify.py and eval only: it is NOT reachable
    from get_provider() or REPOGUARD_AI_PROVIDER."""

    def __init__(self, turns: list[dict]):
        self.turns = list(turns)
        self.turn_index = 0

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        *,
        max_tokens: int | None = None,
        timeout_ms: int | None = None,
    ) -> dict:
        if self.turn_index >= len(self.turns):
            return {"choices": [{"message": {"role": "assistant", "content": "Done"}}]}
        turn = self.turns[self.turn_index]
        self.turn_index += 1
        return {"choices": [{"message": turn}]}
