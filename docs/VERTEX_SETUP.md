# Setting up Google Vertex AI

`repoguard_engine/ai_providers/vertex.py` turns an already-measured dashboard
into prose, or drives the `repoguard fix` tool-calling loop, via Google
Vertex AI's Gemini models — an alternative to the default watsonx.ai
provider. Select it with `REPOGUARD_AI_PROVIDER=vertex` or `--provider
vertex`. See `docs/MULTICLOUD_AI.md` for the architecture.

## 1. Get a GCP project and credentials

Unlike watsonx.ai, there's no separate API key — Vertex AI uses standard
Google Cloud credentials. Two ways to get them:

- **Local development (what this project was verified with):**
  ```bash
  gcloud auth application-default login
  ```
  Opens a browser, logs in with your Google account, and writes Application
  Default Credentials (ADC) to a local file `google-genai` finds
  automatically — no key file to manage.
- **CI / service accounts:** create a service account with the "Vertex AI
  User" role, download its JSON key, and set
  `GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json`.

Either way, make sure the Vertex AI API is enabled for your project (IBM
Cloud console → APIs & Services, or `gcloud services enable
aiplatform.googleapis.com`).

## 2. Install the optional dependency

```bash
pip install -e ".[vertex]"
```

Nothing else in `repoguard` needs this — same optional-extra pattern as
`[ai]` for watsonx.ai.

## 3. Set the environment variables

```bash
# bash / zsh
export VERTEX_PROJECT_ID="<your gcp project id>"
export VERTEX_LOCATION="us-central1"  # optional, this is the default
```

```powershell
# PowerShell (Windows)
$env:VERTEX_PROJECT_ID="<your gcp project id>"
$env:VERTEX_LOCATION="us-central1"  # optional, this is the default
```

`VERTEX_PROJECT_ID` is required even if `gcloud config get-value project`
already has a default set — this stays explicit and reproducible rather
than reading gcloud's ambient config, the same reasoning `AGENTS.md §9`
already gives for never resolving a bare command through ambient PATH.

## 4. Try it

```bash
repoguard analyze demo-repo --summarize --provider vertex
repoguard fix demo-repo --provider vertex
```

If credentials are missing, this prints `Summary unavailable: VERTEX_PROJECT_ID
must be set ...` or the fix loop fails immediately with the same message —
never fabricated text, per `AGENTS.md §4`.

## What was verified before this doc was written

Live-verified this session against a real GCP project
(`gemini-2.5-flash`, `us-central1`), using `gcloud auth application-default
login` credentials — not just a fake-key network check like watsonx.ai's
initial verification, an actual successful round trip:

- A plain `--summarize` call returned real generated prose on the first try.
- A full tool-calling round trip through `repoguard fix`'s exact code path
  (`ChatProvider.chat()`, `watson_agent/tools.py`'s real `TOOL_SCHEMAS`) —
  the model correctly requested `read_source_file`, and after receiving a
  function response produced a coherent final answer.
- **Real finding, not assumed:** the design doc's guess at an OpenAI-
  compatible `Client.chat.completions` surface doesn't exist in
  `google-genai==2.25.0`. The real fit is the stateless
  `client.models.generate_content(model=, contents=<Content list>,
  config=)` — `client.chats.create()` is a *stateful* session object that
  doesn't take a full messages list, so it didn't match how
  `watson_agent/orchestrator.py` rebuilds the message history fresh each
  round.
- **Real finding, not assumed:** `FunctionDeclaration` accepts a plain JSON
  Schema dict directly via its `parameters_json_schema` field —
  `watson_agent/tools.py`'s existing `TOOL_SCHEMAS` (OpenAI-format JSON
  Schema) pass straight through with no conversion needed.
- **Real finding, not assumed:** Gemini 2.5's "thinking" (internal reasoning
  tokens) is deducted from `max_output_tokens` by default. In live testing,
  a 300-token budget left only 66 tokens for the actual answer
  (`thoughts_token_count=201`), truncating the narrative summary to one
  short sentence instead of the requested 2-4. Fixed by setting
  `thinking_config=ThinkingConfig(thinking_budget=0)` on every call — this
  project's summary and tool-selection tasks don't need deep reasoning, and
  disabling it is also strictly faster, which is the whole reason Vertex
  was chosen as the fast provider.
- Gemini doesn't assign call IDs to function calls the way OpenAI/watsonx
  do; `vertex.py` uses the function name itself as the round-trip id. This
  is an internal translation detail, never surfaced to callers.

**Not yet verified:** a full `repoguard fix` run's actual mutation-score
improvement with Gemini as the writer/critic (whether Gemini reliably
invokes tools across a real multi-file fix-loop run, the way
`mistral-small-3-1-24b-instruct-2503` on watsonx.ai did not — see
`PENDING.md` Phase 16 for that finding).
