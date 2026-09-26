# PENDING.md — TestMind AI

Build plan and task tracker. Update status as work progresses; never delete completed items.

> Format (task lists): `- [ ]` pending · `- [-]` in progress · `- [x]` done  
> Format (phase tables): 🔴 Not started · 🟡 In progress · 🟢 Done

---

## Priority traffic light

```
🔴 1 — critical path, no product or demo without this
       phases 0 · 1 · 2 · 3 · 7 · 8 · 11

🟡 2 — rounds out the product, doesn't block the first demo
       phases 4 · 5 · 6 · 9 · 13 · 14

🟢 3 — polish, first thing to cut if time runs short
       phases 10 · 12
```

---

## Phase 0 — Project skeleton
**Priority: 1 (critical)**

| Deliverable | Description | Status |
|---|---|---|
| Folder structure | `repoguard_engine/`, `.bob/`, `demo-repo/`, `docs/`, `bob-evidence/`, `scripts/` | 🟢 |
| `pyproject.toml` | Package `repoguard`, Python >=3.10, deps (incl. playwright, pillow), `repoguard` console script | 🟢 |
| `AGENTS.md` | Project context: what it is, stack, architecture rules, layers, standards | 🟢 |
| `.gitignore` / `.bobignore` | Exclude caches, virtual envs, `repoguard-out/` results | 🟢 |
| `scripts/verify.py` | Phase gate script — `python scripts/verify.py phase0` → PASS | 🟢 |
| `pip install -e .` | Package installs; `repoguard --help` runs all 5 subcommands | 🟢 |

---

## Phase 1 — demo-repo (test fixture)
**Priority: 1 (critical) · Depends on: 0**

| Deliverable | Description | Status |
|---|---|---|
| `shop/pricing.py` | Discount, shipping and loyalty logic | 🟢 |
| `shop/cart.py` | Shopping cart | 🟢 |
| `shop/inventory.py` | Inventory, no tests (intentional gap) | 🟢 |
| `shop/api.py` | FastAPI cart API | 🟢 |
| `web/index.html` | Simple storefront page | 🟢 |
| `tests/` | Tests that run almost all the code but assert very little (on purpose) | 🟢 |

---

## Phase 2 — core: tests, coverage, gaps
**Priority: 1 (critical) · Depends on: 0**

| Deliverable | Description | Status |
|---|---|---|
| `run_tests()` | Runs pytest, returns pass/fail and failures | 🟢 |
| `coverage_report()` | Line coverage per file | 🟢 |
| `scan_repo()` | Maps functions and flags the ones no test names (gaps) | 🟢 |

---

## Phase 3 — Mutation engine
**Priority: 1 (critical) · Depends on: 2**

| Deliverable | Description | Status |
|---|---|---|
| `mutation_test()` | Injects bugs one at a time (own AST engine) and measures how many tests catch | 🟢 |
| Operators | comparison, arithmetic, boolean, constants, `return None`, remove `raise` | 🟢 |
| Determinism | Same input → same result every time (watch out for bytecode caching) | 🟢 |

**This is the product's core feature**: it measures whether tests actually catch bugs, not just whether they execute lines.

---

## Phase 4 — Risk score and dashboard
**Priority: 2 · Depends on: 3**

| Deliverable | Description | Status |
|---|---|---|
| `risk_score()` | Ranks files by `uncovered lines / non-blank lines` (what `compute_risk` actually does). The earlier "complexity × git churn × (1 − detection rate)" description was never implemented; extra terms are Phase 17 §5, added only if stored data shows they predict surviving mutants better | 🟢 |
| `render_dashboard()` | HTML report with before/after, gaps, risk, surviving mutants | 🟡 |

---

## Phase 5 — API check
**Priority: 2 · Depends on: 2**

| Deliverable | Description | Status |
|---|---|---|
| `api_scan()` | Reads a FastAPI app's OpenAPI schema, flags endpoints with no test | 🟢 |
| Smoke test | Calls every `GET` with no required params, catches 5xx errors | 🟢 |

---

## Phase 6 — Visual testing
**Priority: 2 · Depends on: 5**

| Deliverable | Description | Status |
|---|---|---|
| `visual_check()` | Starts the app, takes desktop and mobile screenshots | 🟢 |
| Pixel diff | Compares against a saved baseline | 🟢 |
| Console and accessibility | JS errors, missing `alt`, unnamed controls | 🟢 |

---

## Phase 7 — MCP server
**Priority: 1 (critical) · Depends on: 3**

| Deliverable | Description | Status |
|---|---|---|
| `mcp_server.py` | Exposes 9 tools (scan, tests, coverage, mutation, API, visual, risk, dashboard, watsonx.ai summary) to any MCP client | 🟢 |
| MCP server connection config | Point any client's config at `repoguard mcp` (`.bob/mcp.json` was the Bob-specific example; retired, see `.bob/DEPRECATED.md`) | 🟢 |
| Compact responses | Short summaries by default; full detail only on request | 🟢 |

This phase is the generic MCP integration — usable by any MCP client, not tied to any one agent platform.

---

## Phase 8 — watsonx.ai fix-loop orchestrator (was: Bob modes, rules and skills)
**Priority: 1 (critical) · Depends on: 7**

IBM Bob is retired (`.bob/DEPRECATED.md`); `repoguard_engine/watson_agent/` is
the replacement, built by Claude on `feat/15-watsonx-migration`. It's one
in-process orchestrator, not parallel subagents — see `docs/ARCHITECTURE.md`.

| Deliverable | Description | Status |
|---|---|---|
| Orchestrator loop | `run_fix_loop()`: measure → prioritize by risk → write → critique → re-measure → evidence | 🟢 |
| Test-writer stage | watsonx.ai writes tests that target specific surviving mutants, one file at a time | 🟢 |
| Write guard | `write_test_file` hard-rejects any path outside `tests/` — a tool property, not a prompt rule | 🟢 |
| Critic stage | A second watsonx.ai call reviews the new test against the quality prompt | 🟢 |
| Publisher | `--publish` branches, commits `tests/`, pushes, opens a PR if the gate passes | 🟢 |
| Prompts | Test-writer and critic system prompts, carried forward from `.bob/rules`,`.bob/skills` | 🟢 |
| `scripts/verify.py phase16` | Confirms the write guard and the fail-loud credential check — not a live watsonx.ai call | 🟢 |
| Live tool-calling round trip with real credentials | Not verified — no IBM Cloud account available here; same gap as Phase 15's narrative summary | 🟡 |

---

## Phase 9 — Pipeline and CLI
**Priority: 2 · Depends on: 4, 5, 6**

| Deliverable | Description | Status |
|---|---|---|
| `pipeline.py` | Orchestrates step order, shared by the CLI and the web UI | 🟢 |
| `repoguard analyze` | Measures only, no AI | 🟢 |
| `repoguard fix` | Measures, has watsonx.ai write tests (guarded to `tests/`), critiques, measures again | 🟢 |
| `repoguard gate` | Fails CI if the mutation score is below a minimum | 🟢 |

---

## Phase 10 — Web UI
**Priority: 3 · Depends on: 9**

| Deliverable | Description | Status |
|---|---|---|
| `repoguard serve` | Local web server | 🟢 |
| Live progress | Server-Sent Events showing each step as it runs | 🟢 |
| Metrics | Coverage, mutation score, gaps, endpoints, visual changes | 🟡 |
| Embedded report | Final dashboard shown on the same page | 🟡 |

---

## Phase 11 — Real run via watsonx.ai (was: Real run in Bob)
**Priority: 1 (critical) · Depends on: 8** — 🟢 done, real run, independently re-verified

The old Bob-swarm plan (`phase11-swarm-run-plan.md`) is superseded — Bob is
retired, and the orchestrator is no longer parallel subagents to screenshot.
This phase's original blocker (a real IBM Cloud/GCP account) was cleared in
Phase 16; the actual remaining blocker turned out to be model reliability
(watsonx's fallback model didn't call tools; `gemini-2.5-flash` twice
hallucinated a nonexistent method), fixed this session — see below.

| Deliverable | Description | Status |
|---|---|---|
| First full run | `repoguard fix demo-repo --provider vertex` (`gemini-3.8-flash`) improved demo-repo's tests end to end, with real credentials | 🟢 |
| Evidence | `demo-repo/watson-evidence/01-fix-loop.md` — auto-written, inspected, then discarded per the "never leave it in demo-repo/tests" rule (it's gitignored anyway) | 🟢 |
| Number verification | Mutation score 20.25% (16/79) → **89.87% (71/79)**, coverage 65.1% → 99.1%. Independently re-measured from a clean `run_mutation()` call (not just the fix loop's own printed number): `89.87 71 8 79`, exact match | 🟢 |

This is what gets recorded for the demo: it's the proof that the system works as described.

Getting here took 3 real attempts and 3 real bugs found and fixed, not one clean run:
1. `gemini-2.5-flash` twice wrote a test calling a method (`Inventory.clear()`) that doesn't exist — caught both times by `run_mutation()`'s baseline guard (no false mutation score was ever reported), but the fix loop had no way to self-correct mid-run and `cli.py` crashed with a raw traceback instead of a clean failure (fixed: `fix(cli): repoguard fix fails gracefully...`).
2. Moved to Gemini 3 (`gemini-3.5-flash`/`gemini-3.8-flash`) for better tool-call accuracy, and added a `run_tests` tool (`watson_agent/tools.py`) plus prompt changes (`watson_agent/prompts.py`) requiring the writer/critic to actually execute pytest and see real output before finalizing — real finding, live-verified: Gemini 3's Flash tier 404s at `location=us-central1` (works at `global`); `gemini-3.1-pro` 404s even at `global` on this project.
3. Gemini 3's function-call parts carry a `thought_signature` that must be replayed on the next turn or the API 400s (`google.genai.errors.ClientError: ... Function call is missing a thought_signature`) — `ai_providers/vertex.py` was discarding it; fixed by capturing it from `response.candidates[0].content.parts[*].thought_signature` and replaying it via `Part.thought_signature` on the reconstructed function-call part.

The successful run's critic notes confirm `run_tests` was actually used, not just prompted for — e.g. "Executed `run_tests` on `tests/test_inventory.py`: 25 passed in 0.03s" — grounding the APPROVED verdicts in real execution, not model confidence.

---

## Phase 12 — Final documentation
**Priority: 3 · Depends on: 11**

| Deliverable | Description | Status |
|---|---|---|
| README | What it is, measured results, how to use it | 🟢 (before/after both real now; badge images generated) |
| ARCHITECTURE.md | Diagrams, data contract, MCP tools | 🟡 |
| DEMO.md | 3-minute script with the real numbers from phase 11 | 🔴 |

---

## Phase 13 — Containerization & CI/CD
**Priority: 2 · Depends on: 0** (independent of the Bob swarm — pure engineering, written by Claude)

| Deliverable | Description | Status |
|---|---|---|
| `Dockerfile` + `.dockerignore` | Single-container image serving both `repoguard serve`'s API and static dashboard; bundles `demo-repo/` so the live URL is demoable out of the box | 🟢 |
| Cloud Run readiness | Handled in the Dockerfile's `CMD` (`--host 0.0.0.0 --port ${PORT:-8080}`) rather than changing `cli.py`'s locally-safe defaults | 🟢 |
| CI workflow | `.github/workflows/ci.yml` — `verify.py phase0/phase7`, demo-repo pytest, `repoguard gate demo-repo --threshold 60` on every push/PR; mutation determinism (`phase3`) as its own slower job | 🟢 |
| CD workflow | `.github/workflows/cd.yml` — builds the image, pushes to Artifact Registry, deploys to Cloud Run on push to `main` (or manual dispatch) | 🟢 |
| GCP setup doc | `docs/DEPLOY.md` — one-time steps a human with GCP access must do | 🟢 |
| GCP resources | Artifact Registry repo, `repoguard-deployer` service account + roles, Workload Identity Federation pool/provider scoped to this exact GitHub repo | 🟢 done for real (`gcloud`, real project, real ADC credentials) |
| CD auth | `cd.yml` switched from a static `GCP_SA_KEY` JSON key to Workload Identity Federation — no long-lived GCP secret ever stored in GitHub | 🟢 |

Verified locally before marking done: `docker`'s daemon isn't reachable from
this sandbox (nested containerization blocked), so the `docker build` itself
is unverified — but the exact command the image's `CMD` runs was tested
directly (`repoguard serve --host 0.0.0.0 --port $PORT`, confirmed serving
and `/api/analyze?repo_path=demo-repo` returning real numbers), and
`repoguard gate demo-repo --threshold 60` — the CI job's actual check —
passed for real (65.1% ≥ 60%, exit 0). Both workflow YAML files parse
successfully. The first real `docker build` should happen in CI itself or
on a machine with Docker access before trusting the image blindly.

The GCP side is done for real, not just written and locally checked: the
user has a working `gcloud` ADC login (already used for Vertex AI, Phase
16), so the Artifact Registry repo, service account, IAM bindings, and WIF
pool/provider were all created directly against a real project this
session — see `docs/DEPLOY.md` §1 for the exact commands run and their
real output (project `project-e0ad10c9-0b2f-4dc0-ac6`, project number
`993240087609`). **Still pending, human-only:** `gh` CLI isn't available in
this environment, so the 6 GitHub repo Variables (`docs/DEPLOY.md` §2) have
to be added through the GitHub web UI before the first real deploy can run.

---

## Phase 14 — Next.js dashboard on Vercel
**Priority: 2 · Depends on: 9, 10** (frontend only — no engine changes)

Decision: no Terraform, no new GCP infrastructure for this piece.
`docs/DEPLOY.md` / Cloud Run (Phase 13) is left as-is for the existing
FastAPI service; this phase adds a separate, richer frontend (`web-next/`)
deployed to Vercel that consumes the existing FastAPI endpoints — see
`docs/ARCHITECTURE-front.md` for the route/component breakdown and data
contract. (This section absorbed the former satellite `PENDING-front.md`.)

**Backend gaps this phase depends on**

| # | Gap | Blocks | Status |
|---|---|---|---|
| 1 | `CORSMiddleware` — `REPOGUARD_CORS_ORIGINS` env var (default `localhost:3000`), `GET`+`POST` | any browser call from the frontend | 🟢 |
| 2 | Gate needs no new endpoint — `/api/analyze?gate_threshold=N` already returns `passed_gate` | — | 🟢 |
| 3 | No `POST /api/fix` — the fix loop is CLI-only | Autofix button | 🔴 revisit once the fix loop (Phase 11) *and* Phase 16's `ChatProvider` are both stable, so the endpoint isn't built twice |
| 4 | `POST /api/summary` — body: `/api/analyze`'s dashboard; returns `{ok, text, error, provider}` (PR #27) | `SummaryPanel` | 🟢 |
| 5 | `/api/stream` takes `gate_threshold` (default 80.0) instead of a hardcoded 80% (PR #27) | live-progress gate readout | 🟢 |
| 6 | `provider` on `/api/summary` comes from the provider actually used (`"watsonx"` or `"vertex"`, via `narrative.py`/`get_provider()`), on both `ok` paths | future Autofix result view | 🟢 add it to gap 3's response when that endpoint exists |

**Deliverables**

| Deliverable | Description | Status |
|---|---|---|
| Next.js app scaffold | `web-next/`, calling the existing FastAPI backend, not replacing it | 🟢 |
| `RepoForm` + `ActionBar` | Repo path input, mutation/endpoints/threshold options, Analyze + Gate buttons (Autofix disabled — gap 3) | 🟢 |
| `StreamLog` | Live progress from `/api/stream` (coverage/gaps/risk events) | 🟢 |
| `StatCards` + `GapsList` + `RiskTable` | Coverage, mutation score, gaps, risk ranking — verbatim from `AnalyzeResponse`, no new numbers | 🟢 |
| `SummaryPanel` | AI prose, labeled advisory + which provider generated it (PRs #26/#27) | 🟢 |
| CI split | `frontend-ci.yml` (lint+build, `web-next/**` only) separate from backend `ci.yml`/`cd.yml` (`paths-ignore: web-next/**`) | 🟢 |
| Vercel deploy | Connect repo/subfolder to Vercel; no IaC, config in `vercel.json` / project settings; `NEXT_PUBLIC_REPOGUARD_API_BASE` per environment | 🟢 deployed: https://ibm-bob-mcp-agent-guard.vercel.app/ — `NEXT_PUBLIC_REPOGUARD_API_BASE` now points at the real Cloud Run backend (`https://repoguard-ljm5hefnsq-uc.a.run.app`), `REPOGUARD_CORS_ORIGINS` on the service updated to allow the Vercel origin; verified end-to-end against the live public demo |
| Docs | `docs/ARCHITECTURE-front.md` updated to what's built (real `/api/summary` contract, closed gaps); `docs/ARCHITECTURE.md`'s section now a short summary pointing to it (kept as a satellite so front/back sessions don't edit the same paragraphs); deployed URL in `README.md` and `web-next/README.md`; real dashboard screenshots (light/dark, production build, `demo-repo` with mutation: 65.1%, 20.25% 16/79) in `README.md` → `docs/img/dashboard-*.png` | 🟢 |
| Visual design | Layout, stat cards, gaps list, risk table with score bars, live-progress states, advisory-tagged summary, empty/error states, light + dark, mobile — CSS Modules, no new dependency; display-only formatting (numbers stay verbatim from the API) | 🟢 checked in Chrome against a real `repoguard serve` at 1280px light/dark and 390px, no console errors |

**Verified so far:** `npm run lint` and `npm run build` pass. End-to-end on
`main` (`50fe2e6`): headless Chrome (Playwright) clicked Analyze against
`repoguard serve --port 8010` + `next dev` on 3000 — `GET /api/analyze`,
`GET /api/stream` and `POST /api/summary` all 200, no CORS or console
errors; dashboard showed coverage 65.1%, 4 gap files, risk table, gate FAIL;
`SummaryPanel` showed the advisory title and "Summary unavailable:
WATSONX_APIKEY and WATSONX_PROJECT_ID must be set…". Separately verified
end-to-end against the real public deployment (Vercel → Cloud Run) — same
result, same clean error path, CORS confirmed working.

**Not yet verified:** the `ok=true` summary path (real generated text,
"Generated by vertex" — the deployed service is configured for Vertex, not
watsonx, see Phase 16). `roles/aiplatform.user` on the Cloud Run runtime SA
is granted for real (confirmed in the IAM policy — needed a human to run
it, blocked for an agent session by Claude Code's own permission-grant
restriction, not a project decision). The `[vertex]` extra fix
(`Dockerfile`) is still not on `main`: it was pushed to `fix/cd-cors-vercel-origin`
*after* that branch had already been merged as PR #49, so it never actually
shipped — recovered onto `fix/vertex-import-error-detail`, not yet merged.
Confirmed live, twice, same error both times: `ok=false`,
`"google-genai is not installed"` — check `git log
origin/main..origin/fix/vertex-import-error-detail` before assuming this is
fixed on `main`.

**Known issues**

| Issue | Status |
|---|---|
| `GET /` returned 500 on Windows (`index.html` read as cp1252) | 🟢 fixed (PR #30) |
| `/api/stream` stuck at "Running pytest with coverage…" — `/api/analyze` was `async def` running the pipeline synchronously, blocking the event loop while `web-next` had both open | 🟢 fixed (PR #30) |
| Under `next dev`, `POST /api/summary` fired twice (React StrictMode double mount) — two paid watsonx.ai calls per local test with real credentials | 🟢 fixed (PR #29) (summary requested once, right after `/api/analyze` returns; stale summaries dropped) |
| `web-next` runs `/api/analyze` and `/api/stream` concurrently → two pytest-cov runs sharing `.coverage`/`coverage.json` at fixed paths in the target repo (could erase each other's data) | 🟢 fixed (PR #32) (`measure_coverage()` uses a per-run temp dir; 4 parallel runs all 65.12%) |

---

## Phase 15 — watsonx.ai narrative summary
**Priority: 2 · Depends on: 4** (a text layer on top of already-measured numbers — no new metrics, no engine changes)

`repoguard_engine/narrative.py` turns an already-measured dashboard dict into
plain-English prose via IBM watsonx.ai — advisory text only, never a source
of any number, per `AGENTS.md §4`. Optional dependency (`pip install -e
".[ai]"`), degrades gracefully (`ok=False`, a real error) with no credentials.

| Deliverable | Description | Status |
|---|---|---|
| `narrative.py` | `generate_summary(dashboard)` — prompt built only from measured fields, never invents a number | 🟢 |
| `tool_generate_summary` MCP tool (9th tool) | Compact `{ok, summary}`, detail `{+error}` | 🟢 |
| `repoguard analyze --summarize` CLI flag | Prints the summary or `Summary unavailable: <real error>` | 🟢 |
| `docs/WATSONX_SETUP.md` | Human-only steps: IBM Cloud API key, watsonx project ID, env vars | 🟢 |
| `scripts/verify.py phase15` | Confirms graceful degradation with no credentials — real check, not a live API call | 🟢 |
| Live generation with real credentials | Not verified — no IBM Cloud account available here. SDK call shapes confirmed against the real installed SDK (`ibm-watsonx-ai==1.7.2`) via `inspect.signature`; a call with a fake key reached the real endpoint and got a genuine `403`. Confirm `DEFAULT_MODEL_ID` is available in your project once real credentials exist. | 🟡 |

---

## Phase 16 — Multicloud AI: watsonx.ai + Google Vertex AI
**Priority: 2 · Depends on: 8, 15** — 🟢 done, both stages built and live-verified — see `docs/MULTICLOUD_AI.md`

The user asked for this project to not be single-cloud: watsonx.ai is the
only provider today (`narrative.py`, `watson_agent/client.py`). This phase
extracts a small `ChatProvider` abstraction so Google Vertex AI (or any
future provider) can be added without touching `tools.py`, `prompts.py`, or
the orchestrator loop, plus a way to benchmark models against each other
using the engine's own mutation-score measurement, not a subjective opinion.

Real watsonx.ai credentials were configured and live-tested this session,
which surfaced two real findings driving this phase's urgency: the free-tier
concurrency pool for the best tool-calling model (`llama-3-3-70b-instruct`)
hits `429` under real load, and a smaller model that does respond
(`mistral-small-3-1-24b-instruct-2503`) doesn't reliably honor tool-calling —
a real `repoguard fix demo-repo` run produced zero mutation-score improvement
because the model replied in plain text instead of calling tools. The user
has a separate Vertex AI account with credit and no rate limits, motivating
Vertex as the reliable/fast provider — built and live-verified in the same
session (Stage B): a real Vertex text call and a full tool-calling round
trip both ran against a real GCP project (`gemini-2.5-flash`,
`us-central1`). That same live testing also surfaced two real integrity
bugs, both fixed: `watson_agent/orchestrator.py`'s tool dispatch only
caught `SourceEditRejected` (any other tool error crashed the whole fix
loop), and `core.py`'s `run_mutation()` never verified the unmutated
baseline passes before mutating (let a broken AI-written suite report a
false 100% mutation score). See `docs/VERTEX_SETUP.md` for credentials.

| Deliverable | Description | Status |
|---|---|---|
| `docs/MULTICLOUD_AI.md` | Design doc: architecture, env vars, refactor steps, benchmarking plan, open questions | 🟢 |
| `ai_providers/base.py` | `ChatProvider` protocol, `AIProviderError` | 🟢 |
| `ai_providers/watsonx.py` | `watson_agent/client.py`'s logic, moved here; `narrative.py` unified onto the same `chat()` interface (previously a separate `generate_text()` call) | 🟢 |
| `ai_providers/vertex.py` | Google Vertex AI implementation against `google-genai==2.25.0`; live-verified with real GCP credentials (text call + tool-calling round trip) | 🟢 |
| `narrative.py` / `orchestrator.py` switched to `get_provider()` | No behavior change for watsonx.ai — confirmed live (`phase15`/`phase16`/new `multicloud` check all PASS; a real `--summarize` call with real watsonx credentials still returns real text) | 🟢 |
| `--provider` CLI flag | `repoguard fix --provider` / `repoguard analyze --summarize --provider` override `REPOGUARD_AI_PROVIDER` per call | 🟢 |
| `scripts/benchmark_models.py` | Runs the fix loop against fresh `demo-repo` copies per `(provider, model_id)`, compares real mutation-score deltas | 🔴 deferred — needs live credentials for 2+ providers |

Live cross-provider benchmarking needs real credentials for at least two
clouds — same human-gated situation as `docs/WATSONX_SETUP.md` and Phase 11.

---

## Phase 17 — Measurement history: Postgres, Terraform, data-driven charts
**Priority: 2 · Depends on: 9, 13, 14** — full design in `docs/DATA_PLATFORM.md`, corrected step-by-step Block A plan in its §13 (Session 20)

Stores every measured run (per commit) so trends, persistent surviving
mutants, flaky tests and fix-loop effect become queryable. The engine still
measures; the database only stores; derived values live in SQL views.
Persistence is off unless `REPOGUARD_DATABASE_URL` is set.

A Session 20 planning pass read the actual current code against the design
doc and found ~15 real gaps (rounding, SQLite view portability, an import
cycle, cross-OS fingerprint paths, an unauthenticated write-amplification
risk on `persist=true`, and more) — all corrected in place in
`docs/DATA_PLATFORM.md`, with a concrete step-by-step build order (A1.1
through A3.4, each with exact files and a real `verify.py phase17-*`
check) in its new §13. Build from §13, not the original design sketch.

| Block | Deliverable | Status |
|---|---|---|
| — | `docs/DATA_PLATFORM.md` — schema, views, charts, Terraform layout, build order | 🟢 corrected + step-by-step plan added, §13 |
| A1 | `repoguard_engine/store/` (SQLAlchemy Core, SQLite + Postgres), `[db]` extra | 🔴 |
| A2 | Engine: per-mutant outcomes + stable fingerprints, `junit.xml` per-test outcomes; `pipeline.py` persists | 🔴 |
| A3 | API read routes + `POST /api/runs` ingest (project token) + `repoguard analyze --push` | 🔴 |
| B1 | `infra/terraform/` — Artifact Registry, deployer service account + roles, WIF pool/provider; `infra-ci.yml` (fmt/validate) | 🟢 codifies the Phase 13 identity that already existed for real; `terraform plan` against the live project confirmed "No changes" after `terraform import` — see `infra/terraform/README.md`. Cloud SQL/Secret Manager stay out until Block A (the DB store itself) is built — no infra ahead of the app that would use it |
| B2 | `cd.yml` on Workload Identity Federation (drop `GCP_SA_KEY`) | 🟢 done early, as part of Phase 13 — see `docs/DEPLOY.md` |
| C1 | web-next charts: trend, survival by operator, fix effect, survivors, flaky | 🔴 |
| C2 | Risk heatmap (below the cut line) | 🔴 |
| D | User accounts (below the cut line — optional) | 🔴 |
| — | `verify.py phase17` (round-trip, determinism, after-reference delta 69.62 pp, Postgres service container) | 🔴 |

`terraform apply` and a GCP billing account are human steps — same
situation as `docs/DEPLOY.md`.

---

## Phase 18 — Multi-agent swarm: parallel agent lanes
**Priority: 2 · Depends on: 8 (fix loop, done); 11 (real sequential baseline, done — 89.87%/71/79); Optional: 16 (per-role providers, done) · Shares S2 with 17** — full design in `docs/MULTI_AGENT_SWARM.md`, corrected step-by-step plan (S0–S8) + 15 risks in its §14 (Session 20)

Brings back IBM Bob's parallel swarm design (`.bob/custom_modes.yaml`), rebuilt
in-process: one lane per source file (Test Writer → Verifier → Critic, up to
2 rounds), lanes in parallel in isolated sandboxes, one global Gate
re-measure after fan-in. Kept behind `repoguard fix --swarm` until real runs
show it's faster (H1) and at least as good (H2) as the sequential loop.

**Blocker, not yet cleared:** Phase 18 can't branch until
`feat/11-gemini3-antihallucination` (the `run_tests` tool the lane Verifier
depends on) is merged to `main` — see `docs/MULTI_AGENT_SWARM.md` §14 R1.
**Real limit found:** demo-repo's mutation ceiling is 71/79 (matches the
hand-written reference tests) — the swarm can only *tie* H2 on this
fixture, not beat it; a harder fixture would be an `AGENTS.md §8` ask-first
change (§14 R2).

| Block | Deliverable | Status |
|---|---|---|
| — | `docs/MULTI_AGENT_SWARM.md` — agents, parallelism, file contract, build order, verification | 🟢 corrected against real Phase 11 result + 4 new bugs found, step-by-step plan added, §14 |
| S1 | Parallel mutation workers; `paths_to_mutate` accepts a file (today it silently finds 0 mutants); zero mutants is an error | 🔴 |
| S2 | Per-mutant records (same as Phase 17 A2) | 🔴 |
| S3 | Per-lane sandbox + owned-path write guard | 🔴 |
| S4 | Lane state machine, thread pool, blackboard files, `timeline.jsonl` | 🔴 |
| S5 | Read-only critic with JSON verdict; one revision round | 🔴 |
| S6 | Fan-in, Gate, Publisher, Reporter | 🔴 |
| S7 | Credential-free stub end-to-end test reaching the documented "after" numbers | 🔴 |
| S8 | SSE lane events + web-next lanes view (below the cut line) | 🔴 |
| S9 | Per-role AI providers (needs Phase 16) | 🔴 |
| S10 | "Swarm over MCP" recipe for external MCP clients | 🔴 |
| — | `verify.py phase18` | 🔴 |

---

## Standalone tasks (not phase-blocked)

- [ ] **Create `scripts/verify.py`** — accepts a phase name, runs the relevant checks, outputs PASS/FAIL with numbers pasteable into a PR description
- [ ] **Add `LASTCONTEXT.md` and `PENDING.md` to the project tree** in `README.md` and `AGENTS.md`
- [ ] **Write engine tests** — `repoguard_engine/` has no `tests/` of its own; run `repoguard gate .` and reach ≥ 80% coverage
- [x] **Verify demo-repo baseline numbers** — measured 65.1% coverage, 20.25% mutation (16/79), 4 files with gaps (AST engine; old mutmut numbers were 74.5%/23.6% — now stale)
- [x] **Add `.gitattributes`** — normalize line endings (CRLF warnings on every commit)
- [x] ~~Populate `bob-evidence/`~~ — moot: `bob-evidence/` is retired along with the rest of `.bob/` (see `.bob/DEPRECATED.md`); `repoguard fix` now auto-writes its own run report to `<target-repo>/watson-evidence/` instead
- [x] **Decide on renaming the GitHub repo/local directory** — kept as `ibm-bob-mcp-agent-guard`; it's the hackathon's name, so it stays even though IBM Bob itself is retired
- [x] **Populate `docs/img/`** — `docs/make_results_chart.py` rewritten (it previously printed hardcoded fictional numbers, not a real chart) to render both PNGs from the real AGENTS.md §7 numbers via matplotlib (`docs` optional dependency, added to `pyproject.toml`)
- [x] **CI workflow** — done as part of Phase 13 above (`.github/workflows/ci.yml`), not the standalone `gate.yml` originally sketched in `RUNBOOK.md §7`
- [x] **Write the missing `docs/expected-after-tests/*.py` reference tests** — all 4 files written (`test_pricing_complete.py`, `test_cart_complete.py`, `test_inventory_complete.py`, `test_api_complete.py`). Measured against the real engine: 71 passed, 100% coverage, 89.87% mutation (71/79), 7 of 7 API endpoints tested. Never left inside `demo-repo/tests/` after measuring, per AGENTS.md §7. Also corrected a pre-existing doc error found along the way: `api.py` has 7 endpoints, not the 8 documented everywhere (README, AGENTS.md's directory tree and old baseline table).

---

## Done

- [x] Initialize git repo and connect to GitHub remote
- [x] Create `RUNBOOK.md`
- [x] Expand project tree in `README.md`
- [x] Expand project tree in `AGENTS.md`
- [x] Update `AGENTS.md § 11` with branch-per-phase and `verify.py` gate rules
- [x] Add session-start instruction at top of `AGENTS.md`
- [x] Create `LASTCONTEXT.md` and `PENDING.md`
