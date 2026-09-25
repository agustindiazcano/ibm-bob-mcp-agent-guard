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
| `risk_score()` | Ranks functions: complexity × git churn × (1 − detection rate) | 🟢 |
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
| `mcp_server.py` | Exposes 8 tools (scan, tests, coverage, mutation, API, visual, risk, dashboard) to Bob | 🟢 |
| `.bob/mcp.json` | MCP server connection config | 🟢 |
| Compact responses | Short summaries by default; full detail only on request | 🟢 |

This phase is the Bob integration: without it, Bob has no way to call the engine.

---

## Phase 8 — Bob modes, rules and skills
**Priority: 1 (critical) · Depends on: 7**

| Deliverable | Description | Status |
|---|---|---|
| Orchestrator mode | Runs the full pipeline (diagnose → fix → verify → close) | 🟢 |
| Test Writer subagent | Writes tests that kill specific mutants, in parallel per file | 🟢 |
| Fixer subagent | Repairs failing tests without touching source code | 🟢 |
| Critic subagent | Audits tests it didn't write (independent reviewer) | 🟢 |
| Publisher subagent | Creates a branch and PR with the new tests | 🟢 |
| Rules | Never edit source code, never estimate numbers, minimum assert quality | 🟢 |
| Skills | pytest conventions, how to prioritize mutants by risk | 🟢 |

---

## Phase 9 — Pipeline and CLI
**Priority: 2 · Depends on: 4, 5, 6**

| Deliverable | Description | Status |
|---|---|---|
| `pipeline.py` | Orchestrates step order, shared by the CLI and the web UI | 🟢 |
| `repoguard analyze` | Measures only, no AI | 🟢 |
| `repoguard fix` | Measures, has Bob write tests, measures again | 🔴 |
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

## Phase 11 — Real run in Bob
**Priority: 1 (critical) · Depends on: 8**

| Deliverable | Description | Status |
|---|---|---|
| First full run | The orchestrator mode improves demo-repo's tests end to end | 🔴 |
| Evidence | Screenshot of subagents working in parallel | 🔴 |
| Number verification | Confirm the mutation score rises measurably | 🔴 |

This is what gets recorded for the demo: it's the proof that the system works as described.

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
| GCP setup doc | `docs/DEPLOY.md` — one-time steps a human with GCP access must do (project, Artifact Registry, service account, GitHub secrets/vars) | 🟢 |

Verified locally before marking done: `docker`'s daemon isn't reachable from
this sandbox (nested containerization blocked), so the `docker build` itself
is unverified — but the exact command the image's `CMD` runs was tested
directly (`repoguard serve --host 0.0.0.0 --port $PORT`, confirmed serving
and `/api/analyze?repo_path=demo-repo` returning real numbers), and
`repoguard gate demo-repo --threshold 60` — the CI job's actual check —
passed for real (65.1% ≥ 60%, exit 0). Both workflow YAML files parse
successfully. The first real `docker build` should happen in CI itself or
on a machine with Docker access before trusting the image blindly.

Deploying itself (the `gcloud`/console steps, granting the service account,
adding repo secrets) needs a human with GCP access — Claude can write and
locally verify the Dockerfile and both workflow files, but can't create
cloud resources or hold real cloud credentials.

---

## Phase 14 — Next.js dashboard on Vercel
**Priority: 2 · Depends on: 9, 10** (frontend only — no engine changes)

Decision (this session): no Terraform, no new GCP infrastructure for this
piece. `docs/DEPLOY.md` / Cloud Run (Phase 13) is left as-is for the existing
FastAPI service; this phase adds a separate, richer frontend deployed to
Vercel that consumes the existing `/api/analyze` and `/api/stream` endpoints
— see `docs/ARCHITECTURE.md`'s "Planned: Next.js dashboard on Vercel".

| Deliverable | Description | Status |
|---|---|---|
| Next.js app scaffold | New `web-next/` (or similar), calling the existing FastAPI backend, not replacing it | 🔴 |
| Dashboard charts | Coverage, mutation score, risk ranking — sourced from the same JSON the current dashboard uses, no new numbers invented | 🔴 |
| Action buttons | "Analyze", "Gate", "Autofix with Bob" — call the existing `repoguard` commands/endpoints | 🔴 |
| Vercel deploy | Connect repo/subfolder to Vercel; no IaC, config lives in `vercel.json` / project settings | 🔴 |
| Docs | Update this file, `README.md` and `docs/ARCHITECTURE.md` with the real deployed URL and measured screenshots once built | 🔴 |

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

## Standalone tasks (not phase-blocked)

- [ ] **Create `scripts/verify.py`** — accepts a phase name, runs the relevant checks, outputs PASS/FAIL with numbers pasteable into a PR description
- [ ] **Add `LASTCONTEXT.md` and `PENDING.md` to the project tree** in `README.md` and `AGENTS.md`
- [ ] **Write engine tests** — `repoguard_engine/` has no `tests/` of its own; run `repoguard gate .` and reach ≥ 80% coverage
- [x] **Verify demo-repo baseline numbers** — measured 65.1% coverage, 20.25% mutation (16/79), 4 files with gaps (AST engine; old mutmut numbers were 74.5%/23.6% — now stale)
- [x] **Add `.gitattributes`** — normalize line endings (CRLF warnings on every commit)
- [ ] **Populate `bob-evidence/`** — export first real Bob session to `bob-evidence/01-initial-build.md`
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
