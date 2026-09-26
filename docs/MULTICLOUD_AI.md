# Multicloud AI: watsonx.ai + Google Vertex AI

**Status: design only — nothing in this document is implemented yet.**
`repoguard_engine/watson_agent/` and `narrative.py` are watsonx.ai-only today.
This is the plan for making both provider-agnostic, plus a way to compare
models against each other once that's in place. See `PENDING.md` Phase 17.

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

## Current state (single-provider)

```
repoguard_engine/
├── narrative.py              generate_summary() -- hardcodes ibm_watsonx_ai imports
└── watson_agent/
    ├── client.py              get_chat_model() -- hardcodes ibm_watsonx_ai imports
    ├── tools.py               provider-agnostic already (plain Python + dataclasses)
    ├── prompts.py             provider-agnostic already (plain strings)
    └── orchestrator.py        calls client.get_chat_model() directly
```

The only two places that know about a specific cloud SDK are `narrative.py`'s
`generate_summary()` and `watson_agent/client.py`'s `get_chat_model()`. Both
already return/raise in a normalized shape (`NarrativeResult`, a dict shaped
like `response["choices"][0]["message"]`, `WatsonxCredentialsError`) — the
refactor is about generalizing *those two call sites*, not the tools, prompts,
or orchestrator loop, which don't reference watsonx.ai at all.

## Proposed architecture

A small `ChatProvider` protocol, one implementation per cloud, selected by an
environment variable — the same pattern `AGENTS.md` already uses for
graceful degradation (fail loud on missing config, never fabricate a result).

```
repoguard_engine/
└── ai_providers/
    ├── __init__.py         get_provider() -- reads REPOGUARD_AI_PROVIDER, returns one below
    ├── base.py             ChatProvider protocol: chat(messages, tools=None) -> dict
    ├── watsonx.py           today's watson_agent/client.py, moved here unchanged
    └── vertex.py            new: Google Vertex AI implementation
```

```python
# base.py
from typing import Protocol

class ChatProvider(Protocol):
    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Returns a dict shaped like {"choices": [{"message": {...}}]} --
        the same OpenAI-compatible shape ModelInference.chat() already
        returns, so tools.py/orchestrator.py need zero changes."""
```

Both `narrative.py` and `watson_agent/orchestrator.py` call
`ai_providers.get_provider()` instead of importing a specific SDK. Neither
file needs to know which cloud is configured — same principle as
`core.py` not knowing which CI system calls it.

### Provider selection

```bash
export REPOGUARD_AI_PROVIDER=watsonx   # default, matches today's behavior
export REPOGUARD_AI_PROVIDER=vertex
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

| Step | What | Depends on |
|---|---|---|
| 1 | Extract `base.py`'s `ChatProvider` protocol; move `watson_agent/client.py`'s logic into `ai_providers/watsonx.py` unchanged | — |
| 2 | Point `narrative.py` and `watson_agent/orchestrator.py` at `ai_providers.get_provider()` instead of importing watsonx directly; re-run `phase15`/`phase16` to confirm no behavior change | 1 |
| 3 | Implement `ai_providers/vertex.py`; verify its SDK call shapes against the real installed package the same way `client.py` was verified (fake-credentials call reaching the real endpoint, `inspect.signature` on the chat method) | 1 |
| 4 | `scripts/benchmark_models.py` + a new `scripts/verify.py` phase confirming the benchmark script degrades gracefully with partial credentials | 2, 3 |
| 5 | Docs: this file moves from "design only" to describing what's actually built; `README.md`/`AGENTS.md`/`CLAUDE.md` gain a real multicloud section (mirroring how the watsonx.ai migration updated them) | 1–4 |

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
- Whether `REPOGUARD_AI_PROVIDER` should support per-call override (e.g. a
  `--provider` CLI flag on `repoguard fix`) or stay a single env var for the
  whole process — leaning toward the flag, since benchmarking needs to run
  multiple providers in the same session, but not decided.
