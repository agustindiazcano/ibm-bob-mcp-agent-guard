# Multicloud AI: watsonx.ai + Google Vertex AI

**Status: Stage A implemented (`repoguard_engine/ai_providers/base.py` +
`watsonx.py` + `__init__.py`); Stage B (`vertex.py`) not yet built — needs
real GCP credentials to live-verify the SDK call shape, same rigor already
applied to watsonx.ai.** `narrative.py` and `watson_agent/orchestrator.py`
now call `ai_providers.get_provider()` instead of importing watsonx.ai
directly; `REPOGUARD_AI_PROVIDER` (default `"watsonx"`) and `--provider` on
`repoguard fix`/`repoguard analyze --summarize` select the backend. See
`PENDING.md` Phase 16.

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

## Current state (Stage A implemented)

```
repoguard_engine/
├── narrative.py              generate_summary() -- calls ai_providers.get_provider()
├── ai_providers/
│   ├── __init__.py           get_provider() -- reads REPOGUARD_AI_PROVIDER, default "watsonx"
│   ├── base.py                ChatProvider protocol, AIProviderError
│   ├── watsonx.py              implemented -- moved from watson_agent/client.py
│   └── vertex.py               Stage B -- not built yet, needs live GCP credentials
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

## Architecture (Stage A implemented)

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
export REPOGUARD_AI_PROVIDER=vertex    # Stage B, once vertex.py exists

# or, per call, without touching the environment:
repoguard analyze demo-repo --summarize --provider vertex
repoguard fix demo-repo --provider vertex
```

`get_provider()` raises immediately (fail loud, per `AGENTS.md §9`) if the
selected provider's credentials aren't configured — it never silently falls
back to a different provider than the one asked for.

### `vertex.py`

Google Vertex AI's Gemini models support the same OpenAI-compatible
tool-calling shape via the `google-genai` SDK's `Client.chat.completions`
surface (or `google-cloud-aiplatform`'s `GenerativeModel` with `tools=` —
whichever is actually current when this is implemented needs to be
re-confirmed the same way `client.py`'s watsonx.ai calls were verified
against the real installed SDK via `inspect.signature()`/`help()`, not
assumed from memory).

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
export VERTEX_PROJECT_ID="<gcp-project-id>"
export VERTEX_LOCATION="us-central1"          # optional, sensible default
export VERTEX_MODEL_ID="gemini-<current-flash-or-pro-id>"  # confirm what's
                                                             # actually available
                                                             # in the target
                                                             # project/region
                                                             # before hardcoding
                                                             # a default
```

Same optional-dependency pattern as `[ai]`/`[docs]` in `pyproject.toml`:

```toml
[project.optional-dependencies]
ai = ["ibm-watsonx-ai>=1.7"]
vertex = ["google-genai>=<pin-to-whatever-is-current>"]
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
| 3 | Implement `ai_providers/vertex.py`; verify its SDK call shapes against the real installed package the same way `client.py` was verified (fake-credentials call reaching the real endpoint, `inspect.signature` on the chat method) | 🔴 not started — needs real GCP credentials |
| 4 | `scripts/benchmark_models.py` + a new `scripts/verify.py` phase confirming the benchmark script degrades gracefully with partial credentials | 🔴 deferred — needs live credentials for 2+ providers to mean anything; not this session's goal |
| 5 | Docs: this file moves from "design only" to describing what's actually built; `README.md`/`AGENTS.md`/`CLAUDE.md` gain a real multicloud section (mirroring how the watsonx.ai migration updated them) | 🟡 done for steps 1-2; Vertex-specific doc updates wait on step 3 |

## Non-goals

- Not adding a third provider speculatively (OpenAI, Anthropic, etc.) — the
  ask was specifically watsonx.ai + Google Vertex AI.
- Not building cost tracking or a spend dashboard — out of scope until
  someone asks for it.
- Not changing `tools.py`'s write guard or `prompts.py`'s content at all —
  those are already provider-agnostic and stay exactly as they are.

## Open questions for a human

- Which Vertex AI model(s) to default to, and in which GCP project/region —
  same kind of decision `docs/WATSONX_SETUP.md` already leaves to whoever
  sets up real credentials, not something to guess here.
- ~~Whether `REPOGUARD_AI_PROVIDER` should support per-call override~~ —
  resolved: `get_provider(provider=...)` takes the override, and
  `repoguard fix --provider` / `repoguard analyze --summarize --provider`
  expose it on the CLI (`watsonx` or `vertex`, defaulting to
  `REPOGUARD_AI_PROVIDER`, itself defaulting to `"watsonx"`).
