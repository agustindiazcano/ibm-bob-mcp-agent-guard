# Multicloud AI: watsonx.ai + Google Vertex AI

**Status: both providers implemented and live-verified.**
`repoguard_engine/ai_providers/` has `base.py`, `watsonx.py`, `vertex.py`,
and `__init__.py`'s `get_provider()`. `narrative.py` and
`watson_agent/orchestrator.py` call it instead of importing a cloud SDK
directly; `REPOGUARD_AI_PROVIDER` (default `"watsonx"`) and `--provider` on
`repoguard fix`/`repoguard analyze --summarize` select the backend. See
`PENDING.md` Phase 16 and `docs/VERTEX_SETUP.md` for what was actually
verified live against a real GCP project (not just SDK inspection).

## Why

Two independent reasons, not one:

1. **No single-vendor lock-in.** `docs/WATSONX_SETUP.md` already says plainly
   that no agent working on this repo holds real IBM Cloud credentials —
   the same is true for any one cloud. If TestMind AI only ever runs against
   one provider, a credentials problem with that provider stops the AI
   features entirely (measurement is unaffected either way — that part never
   needed AI, see `AGENTS.md §4`).
2. **Model choice affects the one thing that matters here: does the written
   test actually kill more mutants?** Right now there's no way to know
   whether `ibm/granite-3-8b-instruct` (the current default) is a good
   choice for the test-writer stage, or whether a larger Granite model, a
   Llama model on watsonx.ai, or a Gemini model on Vertex AI would close
   more gaps for the same repo. That's an empirical question the engine can
   already answer — see [Benchmarking](#benchmarking-models) below.

## Current state (both stages implemented)

```
repoguard_engine/
├── narrative.py              generate_summary() -- calls ai_providers.get_provider()
├── ai_providers/
│   ├── __init__.py           get_provider() -- reads REPOGUARD_AI_PROVIDER, default "watsonx"
│   ├── base.py                ChatProvider protocol, AIProviderError
│   ├── watsonx.py              moved from watson_agent/client.py
│   └── vertex.py               google-genai, Vertex AI mode -- live-verified
└── watson_agent/
    ├── tools.py               provider-agnostic (plain Python + dataclasses) -- unchanged
    ├── prompts.py             provider-agnostic (plain strings) -- unchanged
    └── orchestrator.py        calls ai_providers.get_provider() directly
```

`narrative.py` and `watson_agent/orchestrator.py` both call
`ai_providers.get_provider()` and never import a cloud SDK directly.
`generate_summary()` returns a normalized `NarrativeResult` (now including a
`provider` field); the fix loop raises `AIProviderError` (a
`WatsonxCredentialsError`/`VertexCredentialsError` subclass depending on
which provider is active) — same fail-loud contract as before, just
provider-neutral at the call site.

## Architecture (implemented)

A small `ChatProvider` protocol, one implementation per cloud, selected by an
environment variable — the same pattern `AGENTS.md` already uses for
graceful degradation (fail loud on missing config, never fabricate a result).

```python
# ai_providers/base.py
class AIProviderError(RuntimeError): ...

class ChatProvider(Protocol):
    def chat(
        self, messages: list[dict], tools: list[dict] | None = None, *,
        max_tokens: int | None = None, timeout_ms: int | None = None,
    ) -> dict:
        """Returns a dict shaped like {"choices": [{"message": {...}}]} --
        the same OpenAI-compatible shape ModelInference.chat() already
        returns, so tools.py/orchestrator.py need zero changes."""
```

`narrative.py` was also unified onto this single interface (it previously
used a separate completion-style `generate_text()` call) — it now sends one
`{"role": "user", "content": prompt}` message through the same `chat()`,
reading `response["choices"][0]["message"]["content"]` back.

### Provider selection

```bash
export REPOGUARD_AI_PROVIDER=watsonx   # default, matches pre-refactor behavior
export REPOGUARD_AI_PROVIDER=vertex

# or, per call, without touching the environment:
repoguard analyze demo-repo --summarize --provider vertex
repoguard fix demo-repo --provider vertex
```

`get_provider()` raises immediately (fail loud, per `AGENTS.md §9`) if the
selected provider's credentials aren't configured — it never silently falls
back to a different provider than the one asked for.

### `vertex.py`

**The `Client.chat.completions` surface this doc originally guessed at does
not exist in `google-genai==2.25.0`.** Confirmed via `inspect.signature()`/
`model_fields` against the real installed package (see
`docs/VERTEX_SETUP.md`'s verification section for the full list): the real
fit is the stateless `client.models.generate_content(model=, contents=<list
of Content>, config=GenerateContentConfig(...))` — `client.chats.create()`
is a *stateful* session object that keeps its own history and takes one
message at a time, which doesn't match how
`watson_agent/orchestrator.py` rebuilds the full message list fresh every
round. `FunctionDeclaration.parameters_json_schema` accepts a plain JSON
Schema dict directly, so `watson_agent/tools.py`'s existing `TOOL_SCHEMAS`
pass through unconverted. Gemini's "thinking" tokens are deducted from
`max_output_tokens` by default (confirmed live: a 300-token budget left
only 66 for the actual answer) — `vertex.py` disables it
(`ThinkingConfig(thinking_budget=0)`) for both speed and predictable output
length.

```bash
export VERTEX_PROJECT_ID="<gcp-project-id>"
export VERTEX_LOCATION="global"                # optional, this is the default
export VERTEX_MODEL_ID="gemini-3.8-flash"       # optional, this is the default

# Credentials: no separate API key. Either:
gcloud auth application-default login          # local dev -- this is what
                                                # this project was verified with
# or, for CI / service accounts:
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

Default model: `gemini-3.8-flash` at `location="global"` — moved here from
`gemini-2.5-flash`/`us-central1` after a live Phase 11 fix-loop run twice
produced a hallucinated method call; see `docs/VERTEX_SETUP.md`'s "Model
history" section for the full real-verified findings (both Gemini 3 Flash
tiers 404 at `us-central1`, work at `global`; `gemini-3.1-pro` 404s even at
`global` on this project).

Same optional-dependency pattern as `[ai]`/`[docs]` in `pyproject.toml`:

```toml
[project.optional-dependencies]
ai = ["ibm-watsonx-ai>=1.7"]
vertex = ["google-genai>=2.25"]
```

Nothing in the core install needs either extra — same as today.

## Benchmarking models

Once both providers exist behind `ChatProvider`, comparing them is a
measurement problem, not a subjective one — `demo-repo`'s mutation score is
already the engine's own yardstick for "did the test actually help."

Proposed `scripts/benchmark_models.py` (not written yet):

1. For each `(provider, model_id)` pair in a config list, run
   `watson_agent.orchestrator.run_fix_loop("demo-repo", ...)` against a
   **fresh copy** of `demo-repo` (never the real fixture — mutation work
   already copies to a tempdir for this exact reason, `core.py`'s
   `_run_mutant`).
2. Record, per pair: mutation score before/after (from the orchestrator's
   own `FixResult`, already measured by `run_pipeline`, not estimated),
   wall-clock time, and tool-call round trips.
3. Never rank by anything the engine didn't measure — no "this model felt
   better," per `AGENTS.md §4`'s core rule.
4. Output a table (`repoguard-out/benchmark.json` + a printed summary),
   following the same `<target-repo>/repoguard-out/` contract every other
   engine output already uses.

This needs real credentials for at least two providers to run for real — the
same human-gated situation as `docs/WATSONX_SETUP.md` and the still-open
Phase 11 live run. It's written here as a design so the shape is agreed
before any code exists, not because it can be verified in this environment.

## Refactor steps (phased, one branch each per `AGENTS.md §11`)

| Step | What | Status |
|---|---|---|
| 1 | Extract `base.py`'s `ChatProvider` protocol; move `watson_agent/client.py`'s logic into `ai_providers/watsonx.py` | 🟢 done (`feat/16-ai-providers`) |
| 2 | Point `narrative.py` and `watson_agent/orchestrator.py` at `ai_providers.get_provider()`; add `--provider` CLI flag to `repoguard fix`/`analyze --summarize`; `phase15`/`phase16`/new `multicloud` check all PASS, zero behavior change confirmed live with real watsonx credentials | 🟢 done |
| 3 | Implement `ai_providers/vertex.py`; verified its SDK call shapes against the real installed package (`inspect.signature`/`model_fields` on `google-genai==2.25.0`) and live-verified a real text call + a full tool-calling round trip against a real GCP project | 🟢 done |
| 4 | `scripts/benchmark_models.py` + a new `scripts/verify.py` phase confirming the benchmark script degrades gracefully with partial credentials | 🔴 deferred — needs a full fix-loop run with each provider to mean anything; not this session's goal |
| 5 | Docs: this file moves from "design only" to describing what's actually built; `README.md`/`AGENTS.md`/`CLAUDE.md` gain a real multicloud section (mirroring how the watsonx.ai migration updated them) | 🟢 done |

## Non-goals

- Not adding a third provider speculatively (OpenAI, Anthropic, etc.) — the
  ask was specifically watsonx.ai + Google Vertex AI.
- Not building cost tracking or a spend dashboard — out of scope until
  someone asks for it.
- Not changing `tools.py`'s write guard or `prompts.py`'s content *for this
  refactor* — they stayed provider-agnostic through Stages A/B. They were
  later extended in a follow-up Phase 11 session (a new `run_tests` tool,
  prompt instructions requiring it) to fix a real hallucination found live,
  not as part of the multicloud abstraction itself — see
  `docs/VERTEX_SETUP.md`'s "Model history".

## Open questions for a human

- ~~Which Vertex AI model(s) to default to, and in which GCP project/region~~
  — resolved, revised: originally `gemini-2.5-flash`/`us-central1`; moved to
  `gemini-3.8-flash`/`global` after a live hallucination finding (Phase 11).
  `gemini-3.5-flash` is a live-verified alternative via `VERTEX_MODEL_ID`.
  `VERTEX_LOCATION`/`VERTEX_MODEL_ID` env vars and `get_provider(model_id=...)`
  are all overridable for a different project/region's available models.
- ~~Whether `REPOGUARD_AI_PROVIDER` should support per-call override~~ —
  resolved: `get_provider(provider=...)` takes the override, and
  `repoguard fix --provider` / `repoguard analyze --summarize --provider`
  expose it on the CLI (`watsonx` or `vertex`, defaulting to
  `REPOGUARD_AI_PROVIDER`, itself defaulting to `"watsonx"`).
