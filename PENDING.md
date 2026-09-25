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
       phases 4 · 5 · 6 · 9

🟢 3 — polish, first thing to cut if time runs short
       phases 10 · 12
```

---

## Phase 0 — Project skeleton
**Priority: 1 (critical)**

| Deliverable | Description | Status |
|---|---|---|
| Folder structure | `repoguard_engine/`, `.bob/`, `demo-repo/`, `docs/`, `bob-evidence/` | 🟢 |
| `pyproject.toml` | Package `repoguard`, dependencies, `repoguard` console script | 🟢 |
| `AGENTS.md` | Project context: what it is, stack, architecture rules, layers, standards | 🟢 |
| `.gitignore` / `.bobignore` | Exclude caches, virtual envs, results | 🟢 |

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
| Determinism | Same input → same result every time (watch out for bytecode caching) | 🔴 |

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
| Compact responses | Short summaries by default; full detail only on request | 🔴 |

This phase is the Bob integration: without it, Bob has no way to call the engine.

---

## Phase 8 — Bob modes, rules and skills
**Priority: 1 (critical) · Depends on: 7**

| Deliverable | Description | Status |
|---|---|---|
| Orchestrator mode | Runs the full pipeline (diagnose → fix → verify → close) | 🟢 |
| Test Writer subagent | Writes tests that kill specific mutants, in parallel per file | 🔴 |
| Fixer subagent | Repairs failing tests without touching source code | 🟢 |
| Critic subagent | Audits tests it didn't write (independent reviewer) | 🔴 |
| Publisher subagent | Creates a branch and PR with the new tests | 🔴 |
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
| README | What it is, measured results, how to use it | 🟡 |
| ARCHITECTURE.md | Diagrams, data contract, MCP tools | 🟡 |
| DEMO.md | 3-minute script with the real numbers from phase 11 | 🔴 |

---

## Standalone tasks (not phase-blocked)

- [ ] **Create `scripts/verify.py`** — accepts a phase name, runs the relevant checks, outputs PASS/FAIL with numbers pasteable into a PR description
- [ ] **Add `LASTCONTEXT.md` and `PENDING.md` to the project tree** in `README.md` and `AGENTS.md`
- [ ] **Write engine tests** — `repoguard_engine/` has no `tests/` of its own; run `repoguard gate .` and reach ≥ 80% coverage
- [ ] **Verify demo-repo baseline numbers** — `repoguard analyze ./demo-repo` must match: 74.5% coverage, 23.6% mutation, 6/8 endpoints untested
- [ ] **Add `.gitattributes`** — normalize line endings (CRLF warnings on every commit)
- [ ] **Populate `bob-evidence/`** — export first real Bob session to `bob-evidence/01-initial-build.md`
- [ ] **Populate `docs/img/`** — `README.md` references `results-en-dark.png` and `results-en-light.png`; these don't exist yet
- [ ] **CI workflow** — add `.github/workflows/gate.yml` (snippet is in `RUNBOOK.md § 7`)

---

## Done

- [x] Initialize git repo and connect to GitHub remote
- [x] Create `RUNBOOK.md`
- [x] Expand project tree in `README.md`
- [x] Expand project tree in `AGENTS.md`
- [x] Update `AGENTS.md § 11` with branch-per-phase and `verify.py` gate rules
- [x] Add session-start instruction at top of `AGENTS.md`
- [x] Create `LASTCONTEXT.md` and `PENDING.md`
