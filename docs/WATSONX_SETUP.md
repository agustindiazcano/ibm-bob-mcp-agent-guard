# Setting up the watsonx.ai narrative summary

`repoguard_engine/narrative.py` turns an already-measured dashboard (coverage,
mutation score, risk) into a short plain-English summary via IBM watsonx.ai.
It never computes or alters a metric — every number it can mention was
already measured by the engine before it's ever called. See `AGENTS.md §4`.

This is the human half of the setup: getting real IBM Cloud credentials.
No agent working on this repo holds those credentials, so this can't be
automated from here — same situation as `docs/DEPLOY.md`'s GCP setup.

## 1. Get an IBM Cloud API key and a watsonx project

1. Sign in to [IBM Cloud](https://cloud.ibm.com) (or create an account).
2. Create or open a [watsonx.ai project](https://dataplatform.cloud.ibm.com/wx/home) — note its **Project ID** (Project → Manage → General).
3. Create an API key: IBM Cloud console → Manage → Access (IAM) → API keys → Create.

## 2. Install the optional dependency

```bash
pip install -e ".[ai]"
```

Nothing else in `repoguard` needs this — measurement, the CLI, `repoguard
serve`, and MCP tools 1–8 all work with zero AI calls and zero credentials.
Only `narrative.py` / `--summarize` / `tool_generate_summary` import it, and
they degrade gracefully (`ok=False`, a real error) if it's missing.

## 3. Set the environment variables

**`repoguard` does not read `.env` files** (no `python-dotenv`). Putting the
keys in a `.env` does nothing — set them in the same terminal session you
run `repoguard` from. `.env.example` at the repo root lists the variables
as a reference; never commit real values (`.env`/`.env.*` are gitignored,
only `.env.example` is tracked).

```bash
# bash / zsh
export WATSONX_APIKEY="<your IBM Cloud API key>"
export WATSONX_PROJECT_ID="<your watsonx project id>"
export WATSONX_URL="https://us-south.ml.cloud.ibm.com"  # optional, this is the default
```

```powershell
# PowerShell (Windows)
$env:WATSONX_APIKEY="<your IBM Cloud API key>"
$env:WATSONX_PROJECT_ID="<your watsonx project id>"
$env:WATSONX_URL="https://us-south.ml.cloud.ibm.com"  # optional, this is the default
```

These only last for that terminal session. For an MCP client, add them
under that server's `"env"` block in the client's config instead of
relying on ambient environment variables, the same way `repoguard`'s own
PATH pitfalls are handled (see `AGENTS.md §9`).

## 4. Try it

```bash
repoguard analyze demo-repo --summarize
```

If credentials are missing or wrong, this prints `Summary unavailable: <the
real error>` rather than fabricating text — that's the intended behavior,
not a bug, per `AGENTS.md §4`'s "never estimate a metric."

## What was and wasn't verified before this doc was written

- The exact `ibm_watsonx_ai` SDK calls (`Credentials`, `ModelInference`,
  `generate_text`, the `time_limit` param) were checked against the real
  installed SDK (`ibm-watsonx-ai==1.7.2`) via `inspect.signature` — the
  shapes match what `narrative.py` calls.
- A live call with a fake API key reached the real watsonx.ai endpoint and
  got a genuine `403 Forbidden` back — confirmed the network path and
  graceful-degradation behavior work, without a real account.
- **Not verified:** an actual successful generation with real credentials,
  or which model IDs are currently available on your account/region.
  `DEFAULT_MODEL_ID` in `narrative.py` (`ibm/granite-3-8b-instruct`) is a
  reasonable default, not a guarantee — confirm it's available in your
  project once you have real credentials, and pass a different `model_id`
  to `generate_summary()` if not.
