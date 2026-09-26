"""Google Vertex AI ChatProvider (REPOGUARD_AI_PROVIDER=vertex / --provider vertex).

Verified against the actually-installed google-genai==2.25.0 via
inspect.signature()/model_fields (not assumed from memory):
- genai.Client(vertexai=True, project=..., location=...) is the real
  constructor shape.
- The stateful client.chats.create()/Chat.send_message() surface does NOT
  take a plain OpenAI-style messages list (it keeps its own internal
  history and sends one message at a time) -- the design doc's guess at a
  "chat.completions" surface doesn't exist in this SDK. The call that
  actually fits (a full, provider-agnostic message list rebuilt fresh each
  round by watson_agent/orchestrator.py) is the stateless
  client.models.generate_content(model=, contents=<Content list>, config=).
- FunctionDeclaration accepts a plain JSON-Schema dict directly via its
  `parameters_json_schema` field -- watson_agent/tools.py's TOOL_SCHEMAS
  (OpenAI function-calling JSON Schema) can be passed straight through with
  no conversion to Google's own `Schema` type.
- GenerateContentResponse exposes `.function_calls` and `.text` convenience
  properties; a function call has `.name`/`.args` (a plain dict); no call
  `.id` is provided by Gemini (unlike OpenAI/watsonx), so this module uses
  the function name itself as the round-trip id -- self-consistent within
  this translation layer, never surfaced to callers.

Live-verified against a real GCP project: a plain text call, and a full
function-call round trip (model requests a tool, we send back a function
response, model produces final text) -- both worked with gemini-2.5-flash
in an earlier session, and again with gemini-3.5-flash / gemini-3.8-flash
(both text and tool-calling) when the model lineup moved to Gemini 3 for
better resistance to the hallucinated-API-call failures Phase 11 hit twice
with 2.5-flash (see PENDING.md Phase 11 / tools.py's run_tests).

Real finding, not assumed: gemini-3.5-flash and gemini-3.8-flash 404 at
location="us-central1" ("Publisher model ... was not found") but work at
location="global" -- Gemini 3's flash tier isn't regionally available the
way 2.5-flash was. gemini-3.1-pro (the Gemini 3 Pro tier) 404s even at
global on this project -- likely needs separate preview allowlisting;
not used here. DEFAULT_LOCATION is "global" accordingly; anything using
this provider with an older region override in VERTEX_LOCATION needs to
drop it for a Gemini 3 model_id.

Credentials come from Application Default Credentials (gcloud auth
application-default login) or GOOGLE_APPLICATION_CREDENTIALS; there is no
separate API key. google.auth.default() is used as the fail-loud
credential precheck (cheap, no network round trip) so a missing-credentials
failure is instant, before the caller's multi-minute mutation baseline runs
-- same requirement client.py/watsonx.py already satisfy.
"""

from __future__ import annotations

import base64
import json
import os

from .base import AIProviderError

DEFAULT_MODEL_ID = "gemini-3.8-flash"
DEFAULT_LOCATION = "global"


class VertexCredentialsError(AIProviderError):
    """VERTEX_PROJECT_ID is missing, no usable Google credentials were
    found (no gcloud ADC login, no GOOGLE_APPLICATION_CREDENTIALS), or the
    google-genai SDK isn't installed."""


class VertexChatProvider:
    def __init__(self, client, model_id: str) -> None:
        self._client = client
        self._model_id = model_id

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        *,
        max_tokens: int | None = None,
        timeout_ms: int | None = None,
    ) -> dict:
        from google.genai import types

        system_instruction = None
        contents: list = []
        id_to_name: dict[str, str] = {}

        for msg in messages:
            role = msg["role"]
            if role == "system":
                system_instruction = msg["content"]
            elif role == "user":
                contents.append(types.Content(role="user", parts=[types.Part.from_text(text=msg["content"])]))
            elif role == "assistant":
                tool_calls = msg.get("tool_calls") or []
                if tool_calls:
                    parts = []
                    for call in tool_calls:
                        name = call["function"]["name"]
                        try:
                            args = json.loads(call["function"]["arguments"] or "{}")
                        except json.JSONDecodeError:
                            args = {}
                        call_id = call.get("id", name)
                        id_to_name[call_id] = name
                        part = types.Part.from_function_call(name=name, args=args)
                        signature = call.get("thought_signature")
                        if signature:
                            part.thought_signature = base64.b64decode(signature)
                        parts.append(part)
                    contents.append(types.Content(role="model", parts=parts))
                else:
                    contents.append(
                        types.Content(role="model", parts=[types.Part.from_text(text=msg.get("content") or "")])
                    )
            elif role == "tool":
                call_id = msg["tool_call_id"]
                name = id_to_name.get(call_id, call_id)
                try:
                    response = json.loads(msg["content"])
                except (json.JSONDecodeError, TypeError):
                    response = {"result": msg["content"]}
                if not isinstance(response, dict):
                    response = {"result": response}
                contents.append(
                    types.Content(role="user", parts=[types.Part.from_function_response(name=name, response=response)])
                )

        genai_tools = None
        if tools:
            declarations = [
                types.FunctionDeclaration(
                    name=t["function"]["name"],
                    description=t["function"].get("description", ""),
                    parameters_json_schema=t["function"].get("parameters"),
                )
                for t in tools
            ]
            genai_tools = [types.Tool(function_declarations=declarations)]

        # Disable "thinking": Gemini 2.5's internal reasoning tokens are
        # deducted from max_output_tokens, which left as little as 66 of a
        # 300 budget for the actual answer in live testing this session
        # (thoughts_token_count=201). Neither the narrative summary nor the
        # fix-loop's tool selection needs deep chain-of-thought, and turning
        # it off is also strictly faster -- the whole point of picking
        # Vertex as the fast provider.
        config_kwargs: dict = {"thinking_config": types.ThinkingConfig(thinking_budget=0)}
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
        if genai_tools:
            config_kwargs["tools"] = genai_tools
        if max_tokens is not None:
            config_kwargs["max_output_tokens"] = max_tokens
        if timeout_ms is not None:
            config_kwargs["http_options"] = types.HttpOptions(timeout=timeout_ms)
        config = types.GenerateContentConfig(**config_kwargs)

        response = self._client.models.generate_content(
            model=self._model_id,
            contents=contents,
            config=config,
        )
        return self._to_openai_shape(response)

    @staticmethod
    def _to_openai_shape(response) -> dict:
        # Iterates response.candidates[0].content.parts directly rather than
        # the response.function_calls convenience property -- that shortcut
        # returns bare FunctionCall objects and drops each Part's
        # thought_signature, which Gemini 3 (unlike 2.5) requires to be
        # replayed on the next turn's function-call Part or the API rejects
        # the request with 400 INVALID_ARGUMENT ("Function call is missing a
        # thought_signature"). Real finding, live-verified: a 3.8-flash tool
        # call carried an 85-byte signature even with thinking disabled.
        candidates = response.candidates or []
        parts = candidates[0].content.parts if candidates and candidates[0].content else []
        function_call_parts = [p for p in parts if p.function_call]
        if function_call_parts:
            tool_calls = []
            for part in function_call_parts:
                fc = part.function_call
                call = {
                    "id": fc.name,
                    "type": "function",
                    "function": {"name": fc.name, "arguments": json.dumps(fc.args or {})},
                }
                if part.thought_signature:
                    call["thought_signature"] = base64.b64encode(part.thought_signature).decode("ascii")
                tool_calls.append(call)
            return {"choices": [{"message": {"role": "assistant", "content": None, "tool_calls": tool_calls}}]}
        return {"choices": [{"message": {"role": "assistant", "content": response.text or ""}}]}


def get_provider(*, model_id: str | None = None) -> VertexChatProvider:
    """
    Build a VertexChatProvider wrapping a google-genai Client configured for
    Vertex AI.

    Uses VERTEX_PROJECT_ID / VERTEX_LOCATION (default "global") /
    VERTEX_MODEL_ID (default "gemini-3.8-flash", overridden by the model_id
    kwarg if given) env vars; credentials come from Application Default
    Credentials (`gcloud auth application-default login`) or
    GOOGLE_APPLICATION_CREDENTIALS -- see docs/VERTEX_SETUP.md.
    VERTEX_MODEL_ID exists so gemini-3.5-flash / gemini-3.8-flash can be
    A/B'd against real mutation-score deltas without a code change.

    Raises VertexCredentialsError immediately if VERTEX_PROJECT_ID is
    unset, no usable credentials are found, or the SDK isn't installed --
    callers must fail loudly here, never run with a model that silently
    can't be reached.
    """
    project = os.environ.get("VERTEX_PROJECT_ID")
    location = os.environ.get("VERTEX_LOCATION", DEFAULT_LOCATION)
    if model_id is None:
        model_id = os.environ.get("VERTEX_MODEL_ID", DEFAULT_MODEL_ID)

    if not project:
        raise VertexCredentialsError("VERTEX_PROJECT_ID must be set -- see docs/VERTEX_SETUP.md")

    try:
        import google.auth
        from google import genai
    except ImportError as exc:
        raise VertexCredentialsError(
            "google-genai is not installed (pip install 'repoguard[vertex]')"
        ) from exc

    try:
        google.auth.default()
    except Exception as exc:
        raise VertexCredentialsError(
            "No usable Google credentials found -- run `gcloud auth application-default login` "
            f"or set GOOGLE_APPLICATION_CREDENTIALS. See docs/VERTEX_SETUP.md ({exc})"
        ) from exc

    client = genai.Client(vertexai=True, project=project, location=location)
    return VertexChatProvider(client, model_id=model_id)
