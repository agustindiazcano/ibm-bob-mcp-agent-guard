"""ScriptedProvider: a deterministic, credential-free ChatProvider.

It plays the writer and critic roles with canned tool calls instead of a
model, so the real fix loop (tools, write guard, measurement) can run end to
end in CI. The numbers such a run produces are still engine measurements of
whatever tests the script wrote -- the script only replaces the model's
choices, never a metric.

Role is decided from the system prompt: a prompt mentioning "critic" gets
the critic script, anything else the writer script.

Writer script ("reference"): for the file named in the user prompt
(`File: shop/<m>.py` in the sequential loop, `Lane file: ...` in the swarm),
write docs/expected-after-tests/test_<m>_complete.py's content to
`tests/test_<m>_complete.py` (or the owned path the prompt names), run it,
then reply with text. A file with no reference test gets no write.

Critic script: reply with `critic_reply` (plain text for the sequential
loop, a JSON verdict for the swarm), optionally after one run_tests call.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Callable

_FILE_RE = re.compile(r"^(?:Lane file|File):\s*(\S+)", re.MULTILINE)
_OWNED_RE = re.compile(r"^Owned test file:\s*(\S+)", re.MULTILINE)


def _tool_call(call_id: str, name: str, args: dict) -> dict:
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {"id": call_id, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}
                    ],
                }
            }
        ]
    }


def _text(content: str) -> dict:
    return {"choices": [{"message": {"role": "assistant", "content": content}}]}


class ScriptedProvider:
    """Implements ai_providers.base.ChatProvider.chat() with canned replies.

    reference_dir: where test_<module>_complete.py reference files live.
    critic_reply: text the critic returns, or a callable(round_index) ->
        text so a test can script NEEDS_WORK then APPROVED.
    writer_content: optional callable(source_file, round_index) -> str | None
        overriding the reference content (None = write nothing).
    critic_runs_tests: whether the critic calls run_tests before replying.
    """

    def __init__(
        self,
        reference_dir: str | Path,
        *,
        critic_reply: str | Callable[[int], str] = "APPROVED: scripted critic, no findings.",
        writer_content: Callable[[str, int], str | None] | None = None,
        critic_runs_tests: bool = True,
    ) -> None:
        self.reference_dir = Path(reference_dir)
        self.critic_reply = critic_reply
        self.writer_content = writer_content
        self.critic_runs_tests = critic_runs_tests
        # Every chat() call, in order: {"role", "messages"} -- tests assert
        # on what each stage was told (e.g. the round-2 prompt carrying the
        # critic's round-1 findings).
        self.calls: list[dict] = []
        self._rounds: dict[tuple[str, str], int] = {}

    def chat(self, messages: list[dict], tools: list[dict] | None = None, *, max_tokens=None, timeout_ms=None) -> dict:
        system = next((m.get("content") or "" for m in messages if m.get("role") == "system"), "")
        user = next((m.get("content") or "" for m in messages if m.get("role") == "user"), "")
        role = "critic" if "critic" in system.lower() else "writer"
        self.calls.append({"role": role, "messages": copy.deepcopy(messages), "tools": [t["function"]["name"] for t in tools or []]})
        tool_turns = sum(1 for m in messages if m.get("role") == "tool")
        match = _FILE_RE.search(user)
        source = match.group(1) if match else ""

        if role == "writer":
            return self._writer(source, user, tool_turns)
        return self._critic(source, tool_turns)

    def _round(self, role: str, source: str, first_turn: bool) -> int:
        key = (role, source)
        if first_turn:
            self._rounds[key] = self._rounds.get(key, -1) + 1
        return self._rounds.get(key, 0)

    def _writer(self, source: str, user: str, tool_turns: int) -> dict:
        round_index = self._round("writer", source, tool_turns == 0)
        module = Path(source).stem
        owned = _OWNED_RE.search(user)
        target = owned.group(1) if owned else f"tests/test_{module}_complete.py"
        if self.writer_content is not None:
            content = self.writer_content(source, round_index)
        else:
            reference = self.reference_dir / f"test_{module}_complete.py"
            content = reference.read_text(encoding="utf-8") if reference.is_file() else None
        if content is None:
            return _text(f"No test written for {source}: nothing scripted.")
        if tool_turns == 0:
            return _tool_call("call_write", "write_test_file", {"file_path": target, "content": content})
        if tool_turns == 1:
            return _tool_call("call_run", "run_tests", {"file_path": target})
        return _text(f"Wrote {target} for {source} and ran it.")

    def _critic(self, source: str, tool_turns: int) -> dict:
        round_index = self._round("critic", source, tool_turns == 0)
        if self.critic_runs_tests and tool_turns == 0:
            return _tool_call("call_run", "run_tests", {})
        reply = self.critic_reply(round_index) if callable(self.critic_reply) else self.critic_reply
        return _text(reply)
