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

## Phase 4 — Risk score and dashboard
**Priority: 2 · Depends on: 3**

| Deliverable | Description | Status |
|---|---|---|
| `risk_score()` | Ranks files by `uncovered lines / non-blank lines` (what `compute_risk` actually does). The earlier "complexity × git churn × (1 − detection rate)" description was never implemented; extra terms are Phase 17 §5, added only if stored data shows they predict surviving mutants better | 🟢 |
| `render_dashboard()` | HTML report with before/after, gaps, risk, surviving mutants | 🟡 |

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

## Phase 10 — Web UI
**Priority: 3 · Depends on: 9**

| Deliverable | Description | Status |
|---|---|---|
| `repoguard serve` | Local web server | 🟢 |
| Live progress | Server-Sent Events showing each step as it runs | 🟢 |
| Metrics | Coverage, mutation score, gaps, endpoints, visual changes | 🟡 |
| Embedded report | Final dashboard shown on the same page | 🟡 |

---

## Phase 12 — Final documentation
**Priority: 3 · Depends on: 11**

| Deliverable | Description | Status |
|---|---|---|
| README | What it is, measured results, how to use it | 🟢 (before/after both real now; badge images generated) |
| ARCHITECTURE.md | Diagrams, data contract, MCP tools | 🟡 |
| DEMO.md | 3-minute script with the real numbers from phase 11 | 🔴 |

---

## Phase 14 — Next.js dashboard on Vercel
**Priority: 2 · Depends on: 9, 10** (frontend, plus one engine touch: gap 3 added an optional `on_event` progress callback to `run_fix_loop`, which changes no measured behavior)

Decision: no Terraform, no new GCP infrastructure for this piece.
`docs/DEPLOY.md` / Cloud Run (Phase 13) is left as-is for the existing
FastAPI service; this phase adds a separate, richer frontend (`web-next/`)
deployed to Vercel that consumes the existing FastAPI endpoints — see
`docs/ARCHITECTURE-front.md` for the route/component breakdown and data
contract. (This section absorbed the former satellite `PENDING-front.md`.)

**Backend gaps this phase depends on**

| # | Gap | Blocks | Status |
|---|---|---|---|
| 1 | `CORSMiddleware` — `REPOGUARD_CORS_ORIGINS` env var (default `localhost:3000`), `GET`+`POST`. Cloud Run sets it to `https://ibm-bob-mcp-agent-guard.vercel.app` via `cd.yml`'s `env_vars` (PR #49), so it survives every deploy | any browser call from the frontend | 🟢 |
| 2 | Gate needs no new endpoint — `/api/analyze?gate_threshold=N` already returns `passed_gate` | — | 🟢 |
| 3 | `POST /api/fix` — Autofix over HTTP: body `{repo_path, gate_threshold, provider?}`, `Authorization: Bearer <REPOGUARD_FIX_TOKEN>`; streams NDJSON progress + a final `done` with engine-measured `before`/`after`, the test files written, critic notes (advisory) and `provider`. Runs on a temp copy of the repo (target never modified), never publishes, one run at a time (409); 503 when the token isn't configured (`web/fix_job.py`) | Autofix button | 🟡 built, `verify.py phase14fix` PASS, and checked in a browser against a stubbed fix loop. Still to do: attach the token on Cloud Run (`docs/DEPLOY.md` §5, a human step), then a live Vertex run from the Vercel demo |
| 4 | `POST /api/summary` — body: `/api/analyze`'s dashboard; returns `{ok, text, error, provider}` (PR #27) | `SummaryPanel` | 🟢 |
| 5 | `/api/stream` takes `gate_threshold` (default 80.0) instead of a hardcoded 80% (PR #27) | live-progress gate readout | 🟢 |
| 6 | `provider` on `/api/summary` comes from the provider actually used (`"watsonx"` or `"vertex"`, via `narrative.py`/`get_provider()`), on both `ok` paths | Autofix result view | 🟢 also on `/api/fix`'s `done` event, shown in `FixResultPanel` |
| 7 | A nonexistent `repo_path` crashed `/api/analyze` with a raw 500 (`NotADirectoryError`) — now `core._require_repo_dir()` + 400 with `{"detail": "repo_path does not exist or is not a directory: …"}` (PR #47) | a readable error in the dashboard | 🟢 |
| 8 | AI summary on the Cloud Run backend (the public demo) | `SummaryPanel` `ok=true` on the public demo | 🟢 fixed (PR #52) and verified live — real generated text, `provider: vertex`. Needed all three together: `REPOGUARD_AI_PROVIDER=vertex` + `VERTEX_PROJECT_ID` (`cd.yml`), the `[vertex]` extra in the image (`Dockerfile`), and `roles/aiplatform.user` for runtime SA `993240087609-compute@developer.gserviceaccount.com` (granted by hand; not yet in `infra/terraform/`) |

**Deliverables**

| Deliverable | Description | Status |
|---|---|---|
| Next.js app scaffold | `web-next/`, calling the existing FastAPI backend, not replacing it | 🟢 |
| `RepoForm` + `ActionBar` | Repo path input, mutation checkbox, threshold, Analyze + Gate + Autofix buttons, Autofix token field (password input, held in memory only). Gate is coverage-only like `repoguard gate` (`mutation=false`); it used to be a second Analyze button and ran mutation when the box was ticked | 🟢 |
| `StreamLog` | Live progress from `/api/stream` (coverage/gaps/risk events). While `/api/analyze` is still running mutation after the stream ends, a "Running mutation testing" line with an elapsed clock stays active and the badge stays "Running" (it used to say "Done" for the whole mutation run) | 🟢 |
| `StatCards` + `GapsList` + `RiskTable` | Coverage, mutation score, gaps, risk ranking — verbatim from `AnalyzeResponse`, no new numbers | 🟢 |
| `EndpointsList` | Every FastAPI route, "tested"/"no test" and "1 / 7 tested" on `demo-repo`, from `/api/analyze`'s new `endpoints` field (`run_pipeline` already measured it; the route dropped it). Footnote: "tested" is a static mention in a test file, not a request | 🟢 |
| `SummaryPanel` | AI prose, labeled advisory + which provider generated it (PRs #26/#27) | 🟢 |
| `FixResultPanel` | Autofix result: engine-measured before → after (mutation, coverage), the test files written (expandable), critic notes labeled advisory, provider | 🟡 checked against a stubbed fix loop; live run pending (gap 3) |
| CI split | `frontend-ci.yml` (lint+build, `web-next/**` only) separate from backend `ci.yml`/`cd.yml` (`paths-ignore: web-next/**`) | 🟢 |
| Vercel deploy | Connect repo/subfolder to Vercel; no IaC, config in `vercel.json` / project settings; `NEXT_PUBLIC_REPOGUARD_API_BASE` per environment | 🟢 https://ibm-bob-mcp-agent-guard.vercel.app/ wired to the real backend: `NEXT_PUBLIC_REPOGUARD_API_BASE=https://repoguard-ljm5hefnsq-uc.a.run.app` (Production + Preview, type "Config" — it's public by design, the browser calls it); `REPOGUARD_CORS_ORIGINS` on the service allows the Vercel origin (PR #49). Every merge to `main` redeploys automatically; verified end to end against the live public demo |
| Error messages | Unreachable backend → "Can't reach the backend at `<URL>`…" naming both causes (stopped backend / CORS rejection look identical to the browser) (PR #48); non-2xx → the backend's `detail` instead of "analyze failed: 400" (PR #50) | 🟢 verified live |
| Docs | `docs/ARCHITECTURE-front.md` updated to what's built (real `/api/summary` contract, closed gaps); `docs/ARCHITECTURE.md`'s section now a short summary pointing to it (kept as a satellite so front/back sessions don't edit the same paragraphs); deployed URL in `README.md` and `web-next/README.md`; real dashboard screenshots (light/dark, production build, `demo-repo` with mutation: 65.1%, 20.25% 16/79) in `README.md` → `docs/img/dashboard-*.png` | 🟢 |
| Visual design | Layout, stat cards, gaps list, risk table with score bars, live-progress states, advisory-tagged summary, empty/error states, light + dark, mobile — CSS Modules, no new dependency; display-only formatting (numbers stay verbatim from the API) | 🟢 checked in Chrome against a real `repoguard serve` at 1280px light/dark and 390px, no console errors |
| Site restructure | Shared `SiteNav`/`SiteFooter` (`web-next/app/components/site/`) + four screens: **Analyze** (`/`, existing dashboard), **Results** (`/results` — reads `fetchProjects`/`fetchView` from `history.ts`, shows "Run history isn't on this backend yet" until Phase 17 A3 exists), **Project** (`/project`), **Technical** (`/technical`), **AI-assisted dev** (`/ai-development`) — the last three mirror this README's own sections for someone landing on the deployed site | 🟢 PR #58, not verified live in a browser here (`README.md` was found out of date on this — see Session sync below) |
| Provider switch (proposed, Session 24) | A dropdown/toggle on `RepoForm`/`ActionBar` to pick `watsonx` (IBM logo) vs `vertex` per call, instead of the backend's env-var default. **Cheap to build**: `/api/fix` and `/api/summary` already accept and report `provider` (Phase 14 gap 6) and `ai_providers.get_provider()` already handles both (Phase 16, done) — this is a UI-only addition, no backend change. Rationale: makes the "multicloud" story visible to a judge instead of only in `docs/MULTICLOUD_AI.md`, even on runs where watsonx is the weaker option (Phase 16's tool-calling reliability gap) | 🔴 proposed, not started |
| Swarm mode button (proposed, Session 24) | A second mode button next to the sequential fix loop, for `repoguard fix --swarm` once it exists. **Recommendation: ship it disabled/"coming soon" until Phase 18 S3–S8 land**, not wired to silently fall back to the sequential loop — a swarm button that actually runs the sequential loop under the hood would violate `AGENTS.md §4`'s "never fabricate a result" rule by implying parallelism that isn't happening. Revisit once S3 (sandbox) is real | 🔴 proposed, blocked on Phase 18 S3+ |

**Verified so far:** `npm run lint` and `npm run build` pass. End-to-end on
`main` (`50fe2e6`): headless Chrome (Playwright) clicked Analyze against
`repoguard serve --port 8010` + `next dev` on 3000 — `GET /api/analyze`,
`GET /api/stream` and `POST /api/summary` all 200, no CORS or console
errors; dashboard showed coverage 65.1%, 4 gap files, risk table, gate FAIL;
`SummaryPanel` showed the advisory title and "Summary unavailable:
WATSONX_APIKEY and WATSONX_PROJECT_ID must be set…".

**Verified live (public demo, `main` at `c8eca46`):** headless Chrome on
https://ibm-bob-mcp-agent-guard.vercel.app/ → Analyze `./demo-repo` (no
mutation): `GET /api/stream`, `GET /api/analyze`, `POST /api/summary` against
`https://repoguard-ljm5hefnsq-uc.a.run.app` all 200 in ~6 s, no CORS or
console errors; coverage 65.1% (112/172), 4 gap files, gate FAIL — matches
`AGENTS.md §7`. Repo path `./no-such-repo` → "repo_path does not exist or is
not a directory: no-such-repo". Summary panel → "Summary unavailable:
google-genai import failed: No module named 'google'" (gap 8).

**Verified live — `ok=true` summary path, real generated text** (`main` at
`1da4804`, PR #52 — the `[vertex]` extra had to be recovered a second time
after a push-after-merge race ate it out of PR #49; see `LASTCONTEXT.md`
Session 21): `POST /api/summary` against
`https://repoguard-ljm5hefnsq-uc.a.run.app` on the real `demo-repo`
dashboard returned `{"ok": true, "provider": "vertex", "text": "The test
suite covers 65.11627906976744% (112 of 172 lines) of the code, leaving 4
files with coverage gaps, while the mutation score was not measured in
this run...`}` — real generated prose, not fabricated, matching the
measured numbers. `roles/aiplatform.user` on the Cloud Run runtime SA
confirmed in the real IAM policy (granted by hand, blocked for an agent
session by Claude Code's own permission-grant restriction).

**Verified in a browser, scripted (`verify.py phase14ui`):** production
build + real backend on `demo-repo` in Chromium, no stubs: 65.1% (112/172),
4 gap files, 1 / 7 endpoints tested, stream and gate card agree at 60%, Gate
sends `mutation=false`, a real mutation run renders 20.25% (16 / 79) with the
badge on "Running" until then, bad path shows the backend's `detail`, no
console errors. Fails against the previous frontend (stream/gate mismatch,
no endpoints card). Not in CI yet.

**Verified live:** Analyze *with* mutation against the real Cloud Run
service (`GET /api/analyze?repo_path=demo-repo&mutation=true`) — `200` in
2m45s, well under the service's `--timeout=1800`; returned 65.1%
(112/172), mutation 20.25% (16/79), 4 gap files, 1/7 endpoints tested —
exact match to `AGENTS.md §7`.

**Known issues**

| Issue | Status |
|---|---|
| `GET /` returned 500 on Windows (`index.html` read as cp1252) | 🟢 fixed (PR #30) |
| `/api/stream` stuck at "Running pytest with coverage…" — `/api/analyze` was `async def` running the pipeline synchronously, blocking the event loop while `web-next` had both open | 🟢 fixed (PR #30) |
| Under `next dev`, `POST /api/summary` fired twice (React StrictMode double mount) — two paid watsonx.ai calls per local test with real credentials | 🟢 fixed (PR #29) (summary requested once, right after `/api/analyze` returns; stale summaries dropped) |
| `web-next` runs `/api/analyze` and `/api/stream` concurrently → two pytest-cov runs sharing `.coverage`/`coverage.json` at fixed paths in the target repo (could erase each other's data) | 🟢 fixed (PR #32) (`measure_coverage()` uses a per-run temp dir; 4 parallel runs all 65.12%) |
| `/api/stream` was opened without `gate_threshold`, so the stream judged the gate at 80% whatever the form said: at 60% the log said `passed_gate: false` while the gate card said PASS | 🟢 fixed (`streamUrl(repoPath, gateThreshold)`), covered by `phase14ui` |
| Vercel served stale builds after the env var change: `NEXT_PUBLIC_*` is inlined at build time, so saving the variable alone changes nothing; a manual "Redeploy" of an older deployment then became the newest Production build and shadowed the later merges (#48/#50), and a "Promote" of the wrong row rolled back to a `127.0.0.1:8000` build | 🟢 resolved — verified the live JS now contains the Cloud Run URL and PR #48/#50's code (a fresh build from current `main`). Rule: after changing a Vercel env var, Redeploy the **newest `main`** deployment, never an older row. Check which build is live by searching the served JS for the API base URL |

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
| `DEFAULT_PROVIDER` | Vertex AI is now the default provider (was watsonx) — `DEFAULT_PROVIDER` + `resolve_provider_name()` in `ai_providers/`, one place `narrative.py`/`web/fix_job.py` read the provider actually used from. `--provider watsonx` still works | 🟢 PR #62 |
| `scripts/benchmark_models.py` | Runs the fix loop against fresh `demo-repo` copies per `(provider, model_id)`, compares real mutation-score deltas | 🔴 superseded by Phase 19 step 9 (`scripts/eval_fixloop.py`: same idea plus repeats, integrity counts and a held-out fixture) |

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
| A1 | `repoguard_engine/store/` (SQLAlchemy Core, SQLite + Postgres), `[db]` extra; `run_pipeline(persist, project)` stores when `REPOGUARD_DATABASE_URL` is set, opening the DB *before* measuring; `--project` on `analyze`/`gate`; web `/api/analyze`, the fix loop and `tool_generate_summary` never store | 🟢 Session 23 — `verify.py phase17-store` PASS on SQLite **and** a real PostgreSQL 16 (exact equality: stored coverage `65.11627906976744`); `phase17-pipeline` PASS (outputs byte-identical stored vs. not, stored 16/79 = 20.25, bad URL fails in 0.37 s); CI job `store` with a `postgres:16` service |
| A1-gap | **`endpoint_results` has no consumer.** The table is written (decision #6: keep the skeleton) but no route or chart reads it. Build one — e.g. `GET /api/projects/{slug}/endpoints` (A3.1) or an "untested endpoints over time" chart (C1) — or drop the table | 🟢 `GET /api/projects/{slug}/endpoints` (`store/queries.py`, `web/server.py`) — 503 with no database, 404 for an unknown project, 200 with the latest run's endpoints measured (matches demo-repo: 7 endpoints, 1 tested); `verify.py phase17-endpoints` PASS. Frontend wiring (a card/chart consuming it) is separate, not done here |
| A2 | Engine: per-mutant outcomes + stable fingerprints (`MutantRecord` → `repoguard-out/mutants.json`), `junit.xml` per-test outcomes (→ `repoguard-out/tests.json`); built as one commit with Phase 18 S1 (`mutation.py` split out of `core.py`, re-exported) since S2 and A2 are the same work | 🟢 PR #62 — `verify.py phase17-engine` PASS: 79 unique/stable fingerprints identical across 2 runs, fingerprint-stability check on an added function, per-test outcomes 5→71 passed baseline→after-reference, JUnit pass/fail/skip/xfail mapping correct |
| A2-gap | **Per-mutant/per-test records aren't in the database yet** — A2 only writes them to `repoguard-out/mutants.json`/`tests.json`, same as everything else, but nothing loads them into `store/`. Without this, `v_runs` (A1) has no per-mutant history to query, so "persistent surviving mutants" and "flaky tests" (this phase's whole motivation, §1) can't be asked yet. Needs new tables or extending A1's schema | 🟢 Session 28, PR #69/#70 — new `mutants`/`test_results` tables, `SCHEMA_VERSION` 2, `v_survival_by_operator`/`v_persistent_survivors`/`v_flaky_tests` views. `verify.py phase17-mutants-tests` PASS: 79 mutants/5 tests round-trip exactly, `runs.tests_measured` always `True` now (coverage always measures tests) |
| A3 | API read routes + `POST /api/runs` ingest (project token) + `repoguard analyze --push` | 🟢 Session 25 — `GET /api/projects`, `/trend`, `/risk-heatmap`; `POST /api/runs` bearer-token ingest (`repoguard db init/create-project/create-token`), idempotent on `run_id`; `repoguard analyze --push URL` (works without `[db]`/`REPOGUARD_DATABASE_URL`). `verify.py phase17-api` PASS — includes a real `repoguard serve` subprocess + a real CLI push, not just `TestClient`. `web-next/app/results/` (PR #58, `fetchProjects`/`fetchView`) isn't wired to these routes yet — separate task, still open (see C1 row) |
| B1 | `infra/terraform/` — Artifact Registry, deployer service account + roles, WIF pool/provider; `infra-ci.yml` (fmt/validate); **plus Cloud SQL Postgres 16 + Secret Manager** | 🟢 `cicd.tf` codifies the Phase 13 identity that already existed for real (`terraform plan` confirmed "No changes" after `terraform import`). **Session 28, PR #73 — `db.tf` applied for real** (not imported, fresh infra): Cloud SQL instance `repoguard-history`, database, user, `repoguard-database-url` Secret Manager secret, IAM grants for the Cloud Run runtime SA. Wired onto the live service by hand (`--add-cloudsql-instances`, `--update-secrets`) — see `infra/terraform/README.md`. `REPOGUARD_FIX_TOKEN` (Phase 14 gap 3) attached the same way in the same session |
| B2 | `cd.yml` on Workload Identity Federation (drop `GCP_SA_KEY`) | 🟢 done early, as part of Phase 13 — see `docs/DEPLOY.md` |
| C1 | Backend: `/operators`, `/survivors`, `/flaky` read routes. Frontend: web-next charts (trend, survival by operator, fix effect, survivors, flaky) | 🟡 Session 28, PR #71 — backend routes done (`store/queries.py`, `web/server.py`), `verify.py phase17-history-routes` PASS (404 unknown project, real per-operator/per-mutant data over HTTP). **Frontend charts themselves still 🔴** — `web-next/app/results/` isn't wired to any of these routes yet. `/fix-effect` still needs a `fix_sessions` table (separate task, not started) |
| C2 | Risk heatmap (below the cut line) | 🔴 |
| D | User accounts (below the cut line — optional) | 🔴 |
| — | `verify.py phase17` (round-trip, determinism, after-reference delta 69.62 pp, Postgres service container) | 🟢 all Phase 17 checks (`phase17-store`, `phase17-pipeline`, `phase17-endpoints`, `phase17-api`, `phase17-mutants-tests`, `phase17-history-routes`, `phase17-engine`) are now wired and running in CI |

A real GCP billing account was confirmed available (trial, Session 28) —
`terraform apply` for `db.tf` is done; a bare-instance Cloud SQL bills
continuously while it exists (unlike Cloud Run), so `terraform destroy
-target=google_sql_database_instance.history` when it's no longer needed
(e.g. after a demo) — see `infra/terraform/README.md`.

Decisions #2–#6 were resolved by the user in Session 23 (raise on write
failure; slug precedence as recommended; `passed_gate` only in views; no web
writes until per-project tokens; keep `endpoint_results` as a skeleton) —
see `docs/DATA_PLATFORM.md` §13. #1 (JUnit test id) is still open. A2
landed in PR #62 (JSON-only) and its SQL-store gap closed in Session 28
(A2-gap, PR #69/#70). Next step: **C1 frontend** (wire `web-next/app/results/`
to the now-real API), or wiring the new `verify.py` checks into CI.

---

## Phase 18 — Multi-agent swarm: parallel agent lanes
**Priority: 2 · Depends on: 8 (fix loop, done); 11 (real sequential baseline, done — 89.87%/71/79); Optional: 16 (per-role providers, done) · Shares S2 with 17** — full design in `docs/MULTI_AGENT_SWARM.md`, corrected step-by-step plan (S0–S8) + 15 risks in its §14 (Session 20)

Brings back IBM Bob's parallel swarm design (`.bob/custom_modes.yaml`), rebuilt
in-process: one lane per source file (Test Writer → Verifier → Critic, up to
2 rounds), lanes in parallel in isolated sandboxes, one global Gate
re-measure after fan-in. Kept behind `repoguard fix --swarm` until real runs
show it's faster (H1) and at least as good (H2) as the sequential loop.

**Blocker cleared:** `run_tests`, the tool the lane Verifier depends on
(`docs/MULTI_AGENT_SWARM.md` §14 R1), reached `main` with PR #45.
**Real limit found:** demo-repo's mutation ceiling is 71/79 (matches the
hand-written reference tests) — the swarm can only *tie* H2 on this
fixture, not beat it; a harder fixture would be an `AGENTS.md §8` ask-first
change (§14 R2).

| Block | Deliverable | Status |
|---|---|---|
| — | `docs/MULTI_AGENT_SWARM.md` — agents, parallelism, file contract, build order, verification | 🟢 corrected against real Phase 11 result + 4 new bugs found, step-by-step plan added, §14 |
| S0 | Groundwork: `_run_chat_stage` → `StageResult` with injectable toolset; `run_fix_loop(model=...)`; wall time per phase/stage in `FixResult` + evidence; `testing/ScriptedProvider`; `verify.py phase18-seq-stub` + CI job `fix-loop-stub` | 🟢 Session 23. Measured with no credentials: 86.08% (68/79), 362/367 lines, 56 passed, identical across 3 runs |
| S1 | Parallel mutation workers (`mutation.py`, split out of `core.py`); `paths_to_mutate` accepts a single file; empty scope raises `NoMutantsError`; sham-mutant control (`MutationEnvironmentError`) | 🟢 PR #62 — `verify.py phase18-s1` PASS: workers=1 and workers=4 both score 20.25% (16/79), identical surviving-mutant IDs; file-scoped runs sum to 79/16; not yet wired into `ci.yml` (see Phase 17's `verify.py phase17` row) |
| S2 | Per-mutant records (same as Phase 17 A2) | 🟢 PR #62, same commit as A2 above |
| S3 | Per-lane sandbox + owned-path write guard | 🟢 `swarm/sandbox.py` (`lane_sandbox`, `SandboxLeak`, import-isolation probe) + `swarm/guard.py` (`writer_toolset`/`critic_toolset`, wraps `watson_agent/tools.py` without modifying it); `verify.py phase18-s3` PASS: owned write succeeds, 6 out-of-scope paths (source, another lane's file, `conftest.py`, `..` escape, absolute path into the real repo) all `SourceEditRejected`, critic has no write tool, sandbox cleaned up on both normal exit and an exception, real demo-repo byte-identical throughout |
| S4 | Lane state machine, thread pool, blackboard files, `timeline.jsonl` | 🟢 `swarm/blackboard.py` (schema-tagged, atomic writes, `.test.py.txt`-only snapshot guard, `Timeline` behind a lock), `swarm/plan.py` (`build_plan`, no cap, posix-normalized join keys), `swarm/verify.py` (suite-first Verifier, join by fingerprint, `newly_covered` lines), `swarm/lane.py` (`WRITING→VERIFYING→ACCEPTED\|NO_GAIN\|FAILED`, best-round-wins ranking, any exception → `FAILED`), `swarm/runner.py` (sandboxes created serially up front via `ExitStack`, one shared mutation pool, lanes in their own `ThreadPoolExecutor`); `verify.py phase18-s4` PASS: 4/4 lanes `ACCEPTED` round 1 with real kills, `regressed == []`, `timeline.jsonl` shows 4 overlapping lane spans, every recorded sandbox gone, real `tests/` untouched, `workers=1`/`workers=4` identical `verify-1.json`, a permanently-failing writer ends `FAILED` after 2 rounds, a raising writer script is caught not propagated, demo-repo byte-identical throughout. No critic step (S5), no fan-in/Gate (S6), no `--swarm` CLI/web entry point yet. |
| S5 | Read-only critic with JSON verdict; one revision round | 🔴 |
| S6 | Fan-in, Gate, Publisher, Reporter | 🔴 |
| S7 | Credential-free stub end-to-end test reaching the documented "after" numbers | 🔴 |
| S8 | SSE lane events + web-next lanes view (below the cut line) | 🔴 |
| S9 | Per-role AI providers (needs Phase 16) | 🔴 |
| S10 | "Swarm over MCP" recipe for external MCP clients | 🔴 |
| — | `verify.py phase18` | 🔴 |

---

## Phase 19 — Evaluation & guardrails for the AI fix loop
**Priority: 2 · Depends on: 8, 11 (done) · Shares G4 with Phase 18 S1/S2** — plan in `docs/EVAL_GUARDRAILS_PLAN.md`, build steps in `docs/EVAL_GUARDRAILS_IMPLEMENTATION.md` (Session 23)

The fix loop is guarded against damage (writes only under `tests/`) but not
against gaming its own score or leaking. Measured in Session 23 on throwaway
`demo-repo` copies, with the real tool/engine functions:

- **P1:** a test with zero behavioral assertions that asserts the source files' hashes → mutation **100% (79/79)**, above the honest reference's 89.87% (71/79). The baseline guard doesn't catch it, because the test passes on the original code.
- **P2:** a model-written test read `REPOGUARD_FIX_TOKEN` and got it back through `run_tests`' output. Every pytest subprocess inherits the full server environment.
- **P3/P4:** `write_test_file` accepts overwriting `tests/test_cart.py` with `""` and writing `tests/conftest.py`.
- **P5:** coverage counts `tests/` itself: 65.1% (112/172) today vs **60.26% (91/151)** source-only.

Also found by reading the code: `--publish` gates on coverage only; a
harness error in `_run_mutant` counts as killed; a failing AI suite crashes
`run_fix_loop` before the evidence is written; no repetition, so flaky tests
go unnoticed; no benchmark beyond one live run on one fixture.

| Step | ID | Deliverable | Status |
|---|---|---|---|
| 0 | — | `docs/EVAL_GUARDRAILS_PLAN.md` + `docs/EVAL_GUARDRAILS_IMPLEMENTATION.md`, README section | 🟢 |
| 1 | G1 | `core.pytest_env()` allow-list, used by `measure_coverage`, `run_mutation`, `_run_mutant`, `tools.run_tests` | 🟢 Session 27 — canary secrets (`REPOGUARD_FIX_TOKEN`, `WATSONX_APIKEY`) confirmed absent from `run_tests` subprocess output |
| 2 | G2 | `watson_agent/policy.py` static test-file policy inside `write_test_file` — **needs approval (D1, `AGENTS.md §8`)** — approved | 🟢 Session 27 — 9 attack rules fire, 0 false positives on `docs/expected-after-tests/*.py` + `demo-repo/tests/*.py` |
| 3 | G3 | `watson_agent/acceptance.py`: 3× repetition, no-op canary, test-ID preservation, quarantine | 🟢 Session 27 — policy bypass, canary, flaky-repetition, vandalism (missing-ID) and whole-suite state-bleed all caught; the 4 reference files pass acceptance unmodified |
| 4 | G4 | Sham mutant + outcome classes (shared with Phase 18 S1/S2) + monotonic kill set | 🟢 Session 27 — harness `error` is its own outcome class, no longer silently counted as `killed`; `run_mutation` guards `total == 0` |
| 5 | G5 | `FixResult.status`/`integrity`, evidence always written, publish gate on mutation gain + integrity | 🟢 Session 27 |
| 6 | G6 | Source-only coverage — **needs approval (D9)**: moves 65.1% → 60.26%, and the `ci.yml` threshold of 60 needs a decision | 🟢 Session 27 — approved; `ci.yml` gate threshold moved to `60.0`; re-measured directly (not via the stale `repoguard` console script, see Session 27 pitfall below): 60.2649% (91/151) |
| 7 | E1 | `ai_providers/scripted.py` + 8 attack scripts + `verify.py phase19` in CI (8/8 stopped, honest run 71/79) | 🟢 |
| 8 | O1 | `repoguard-out/fix_run.json` structured run record | 🟢 Session 27 — implemented per `docs/EVAL_GUARDRAILS_IMPLEMENTATION.md §9`; fixed two crash bugs found while validating it (`_write_fix_run` called but never defined — `NameError` on every `run_fix_loop` call; `_timing_section` joined `tool_calls` as strings after this same change made them dicts — `TypeError`). See "Known issue" below before assuming `verify.py phase19` is a clean PASS |
| 9 | E2 | `scripts/eval_fixloop.py` (K = 3 × provider/model × fixture) — credentialed, approved | 🟡 built: `scripts/eval_fixloop.py` runs K times per (provider, model) × fixture pair from `eval/matrix.json`, reporting ΔMS, gap closure, validity, integrity violations, and cost as min/median/max. Human-gated: requires real credentials per provider |
| 10 | E3 | Held-out fixture `eval-fixtures/<name>/` — **needs approval (D3)** | 🟢 approved (D3: accounting ledger domain) and verified in CI: `eval-fixtures/ledger/` (package + weak `tests/` + `reference-tests/`), `verify.py phase19-e3` wired into `ci.yml` (`guardrails-phase19`). Measured in CI: baseline coverage 52.17% (24/46), mutation 19.18% (14/73); ceiling coverage 100.0% (60/60), mutation 69.86% (51/73). `eval/matrix.json` ceiling set to 51 |
| 11 | E4 | Real-fault protocol on a BugsInPy subset — **needs approval (D4)** | 🔴 |
| 12 | O2 | NDJSON `guard` events + integrity badge (below the cut line) | 🔴 |
| 13 | E5 | Pynguin control / TestGenEval subset (below the cut line) | 🔴 |
| — | — | `verify.py phase19` | 🟡 timeout raised 1800s → 3600s (measured: baseline 290s + after-with-71-tests 362s, real mutation on a Windows dev box, plus G3's per-file/whole-suite pytest subprocess overhead) — rerun in flight, see Known issue |

**Known issue (Session 27, not blocking):** a direct `run_mutation` timing measurement with the
4 reference test files in place (no fix loop, no guardrails in the path) scored **88.61%
(70/79)**, not the `AGENTS.md §7`-documented **89.87% (71/79)** that E1's `honest` check asserts
exactly. Core numbers are unaffected — the `AGENTS.md §7` baseline (20.25%, 16/79, no guardrails
in the path either) re-measured identical. Read as mutation-score flakiness on this Windows box
(no repetition guard on `run_mutation` itself, only on G3's newly-written-test acceptance gate),
not a functional regression in G1-G6, per user decision this session. Revisit if it recurs.

**Session 27 pitfall (worth its own `AGENTS.md §9` entry):** the `repoguard` console script's
editable install pointed at a sibling worktree (`ibm-bob-mcp-agent-guard-phase17-18`), not this
checkout — running bare `repoguard analyze ...` here silently measured *that* branch's code
(showed the old 65.1% coverage, not this session's 60.3%). Fixed with
`pip install -e ".[ai,vertex,db,docs]"` from this checkout; anyone with parallel worktrees should
check `pip show repoguard`'s "Editable project location" before trusting a bare CLI run.

### Verified CI & Guardrails Results (Run 36295730583)

| Test Suite / Job | Target / Scope | Result | Execution Time |
|---|---|---|---|
| **`quality-gate`** | Phase 0 skeleton, Phase 7 compact MCP, `demo-repo` pytest, 60.0% coverage gate | ✅ **PASS** | 30s |
| **`guardrails-phase19`** | G1 (env allow-list), G2 (static AST policy), G3 (acceptance gate) | ✅ **PASS** | 40s |
| **`mutation-determinism`** | Phase 3 AST mutation engine determinism (two runs on `demo-repo`) | ✅ **PASS** | 2m 17s |
| **`store`** | Phase 17 A1-A3: SQLite + Postgres 16 round-trip, pipeline persistence, endpoints, API routes | ✅ **PASS** | 3m 23s |
| **`fix-loop-stub`** | Phase 18 S0 sequential fix-loop with `ScriptedProvider`, tools, timing, evidence | ✅ **PASS** | 3m 33s |
| **`engine-parallel-mutation`** | Phase 18 S1 parallel workers (workers=1 vs workers=4), single-file scope, Phase 17/18 per-mutant records | ✅ **PASS** | 3m 35s |
| **`frontend-ci`** | `web-next` npm lint + build | ✅ **PASS** | 26s |

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

