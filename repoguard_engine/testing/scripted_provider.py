"""ScriptedProvider: a ChatProvider that answers from a script instead of a
model, so the fix loop can be exercised end to end with no credentials.

It is deliberately never wired into ai_providers.get_provider(): the only way
to use it is to pass it as run_fix_loop(..., model=ScriptedProvider(...)).
That keeps multicloud's "unknown provider fails loud" check true, and means no
environment variable can swap a real provider for a fake one.

The tools it calls are the real ones (write_test_file's tests/-only guard,
run_tests' real pytest subprocess), executed by the orchestrator exactly as
for a live model. Only the model's choices are scripted, and every number
still comes from the engine's re-measure.
"""

from __future__ import annotations

import itertools
import json
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# role, this stage's messages so far -> the assistant message to return.
Script = Callable[[str, list[dict]], dict]

_FILE_LINE = re.compile(r"^File: (\S+)", re.MULTILINE)


@dataclass
class ScriptedCall:
    """One chat() call as the provider received it."""

    role: str
    messages: list[dict]
    tools: list[str]


class ScriptedProvider:
    """
    Answers chat() from scripts keyed by stage role ("writer", "critic").

    The role comes from the stage's system prompt, so the orchestrator needs
    no test-only hook. A role with no script, or a system prompt that matches
    no role, raises ValueError instead of returning an empty answer. Every
    call is recorded in `calls` for tests to assert on.
    """

    def __init__(self, scripts: dict[str, Script]):
        self.scripts = scripts
        self.calls: list[ScriptedCall] = []
        self._ids = itertools.count(1)
        self._lock = threading.Lock()

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        *,
        max_tokens: int | None = None,
        timeout_ms: int | None = None,
    ) -> dict:
        role = _role_of(messages[0]["content"])
        try:
            script = self.scripts[role]
        except KeyError:
            raise ValueError(f"ScriptedProvider has no script for role {role!r}") from None
        with self._lock:
            self.calls.append(
                ScriptedCall(role=role, messages=list(messages), tools=[t["function"]["name"] for t in tools or []])
            )
        message = script(role, messages)
        for call in message.get("tool_calls") or []:
            with self._lock:
                call.setdefault("id", f"call_{next(self._ids)}")
        return {"choices": [{"message": message}]}


def reference_writer(reference_dir: str | Path, *, target_for: Callable[[str], str] | None = None) -> Script:
    """
    Writer script: for the stage's `File: shop/<m>.py`, write
    <reference_dir>/test_<m>_complete.py's content with write_test_file, run
    it with run_tests, then report the exit code. With no reference file for
    that module it writes nothing and says so.

    target_for maps the source file to the test path to write; the default is
    tests/test_<m>_complete.py, the layout docs/expected-after-tests/ uses.
    """
    reference_dir = Path(reference_dir)

    def script(_role: str, messages: list[dict]) -> dict:
        match = _FILE_LINE.search(messages[1]["content"])
        if match is None:
            return _text("No 'File:' line in the prompt; nothing written.")
        source = match.group(1)
        module = Path(source).stem
        reference = reference_dir / f"test_{module}_complete.py"
        target = target_for(source) if target_for else f"tests/test_{module}_complete.py"

        step = _assistant_turns(messages)
        if step == 0:
            if not reference.is_file():
                return _text(f"No reference test for {source}; nothing written.")
            return _tool_call("write_test_file", file_path=target, content=reference.read_text(encoding="utf-8"))
        if step == 1:
            return _tool_call("run_tests", file_path=target)
        result = _last_tool_result(messages)
        return _text(f"Wrote {target}; run_tests exit_code={result.get('exit_code')}.")

    return script


def approving_critic(_role: str, messages: list[dict]) -> dict:
    """Critic script: run the whole tests/ suite, then APPROVED if it passed,
    NEEDS-WORK otherwise. Never writes a file."""
    if _assistant_turns(messages) == 0:
        return _tool_call("run_tests")
    result = _last_tool_result(messages)
    if result.get("passed"):
        return _text("APPROVED")
    return _text(f"NEEDS-WORK: run_tests failed (exit_code={result.get('exit_code')}).")


def _role_of(system_prompt: str) -> str:
    first_line = system_prompt.splitlines()[0] if system_prompt else ""
    if "test-writer" in first_line:
        return "writer"
    if "critic" in first_line:
        return "critic"
    raise ValueError(f"ScriptedProvider can't tell the stage role from system prompt {first_line!r}")


def _assistant_turns(messages: list[dict]) -> int:
    return sum(1 for m in messages if m.get("role") == "assistant")


def _last_tool_result(messages: list[dict]) -> dict:
    for message in reversed(messages):
        if message.get("role") == "tool":
            try:
                return json.loads(message["content"])
            except (json.JSONDecodeError, TypeError):
                return {}
    return {}


def _text(content: str) -> dict:
    return {"role": "assistant", "content": content}


def _tool_call(name: str, **arguments: str) -> dict:
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [{"type": "function", "function": {"name": name, "arguments": json.dumps(arguments)}}],
    }
