> **Read `LASTCONTEXT.md` and `PENDING.md` at the start of every session.**

# Project Context: TestMind AI

## 1. Role
You are a senior Python engineer and QA specialist. You write small, typed, testable code and you never claim a result you did not measure.

## 2. What this project is
TestMind AI measures whether a Python repo's tests actually catch bugs, then uses IBM Bob agents to write the missing tests.
- **Engine** (`repoguard_engine/`, CLI `repoguard`): deterministic measurements — pytest, coverage, AST mutation testing, untested functions, FastAPI endpoint checks, visual regression, risk score, HTML dashboard.
- **Bob layer** (`.bob/`): an orchestrator mode plus subagent modes that call the engine through MCP and write tests.
- **Entry points:** Bob IDE (MCP stdio), terminal (`repoguard analyze | fix | gate | serve | mcp`), web UI (`repoguard serve`).
- The product name is TestMind AI; the CLI, package and MCP server are still named `repoguard`.

## 3. Tech stack
Python ≥ 3.10 · pytest · coverage.py · stdlib `ast` (own mutation engine, no mutmut/Stryker) · MCP Python SDK (FastMCP, stdio) · FastAPI + uvicorn + SSE (web UI) · httpx TestClient (API checks) · Playwright Chromium + Pillow (visual) · matplotlib (docs chart only).

## 4. Architecture rules (non-negotiable)
- **The AI decides, the engine measures.** Every number (coverage, mutation score, risk, endpoints, visual diff) must come from an engine function. Never estimate, round up or extrapolate a metric.
- **Source code is the reference.** Agents that write tests may only edit `tests/`. If a new test fails against the original code, the test is wrong unless there is evidence of a real bug; mark that as `xfail(reason="possible bug: ...")`, never fix source to make a test pass.
- **Determinism.** Same repo in, same numbers out. Mutation runs use `PYTHONDONTWRITEBYTECODE=1`; visual checks disable animations and wait for `networkidle`. Any change that makes two identical runs differ is a bug.
- **Layering.** `core.py` has no web, MCP or CLI code. `api_check.py` and `visual.py` depend only on `core`. `pipeline.py` orders the steps. `cli.py`, `mcp_server.py` and `web/server.py` are thin adapters over `pipeline`/`core`.
- **Outputs.** Engine functions return a dict and write `repoguard-out/<name>.json` in the target repo. That folder is the contract between agents: subagents don't share memory, so they communicate through these files.
- **Compact MCP responses.** MCP tools return summaries by default and full data only with `detail=True`. Every response stays in Bob's context and is resent each turn; don't add fields to the compact output without a reason.
- **Never print to stdout in the MCP server.** stdio is the protocol channel; stray output corrupts it. Use stderr or return values.

## 5. Directory layout
```
ibm-bob-mcp-agent-guard/
├── .bob/
│   ├── custom_modes.yaml             Six modes: orchestrator, analyzer, fixer, gate, visual-agent, reporter
│   ├── mcp.json                      Registers `repoguard mcp` as the MCP server for Bob
│   ├── rules/
│   │   ├── 01-tests-only.md          Fixer only writes under tests/
│   │   ├── 02-measure-dont-guess.md  Always measure before proposing a fix
│   │   └── 03-test-quality.md        Mutation-resistant assertion standards
│   └── skills/
│       ├── mutation-hunting/SKILL.md     How to kill surviving mutants
│       └── pytest-conventions/SKILL.md   Fixture, parametrize, conftest conventions
│
├── repoguard_engine/
│   ├── __init__.py
│   ├── core.py           measure_coverage · find_coverage_gaps · run_mutation · compute_risk · build_dashboard_data
│   ├── api_check.py      find_untested_endpoints (AST) · run_endpoint_smoke_tests (httpx)
│   ├── visual.py         capture_screenshot · pixel_diff · collect_console_logs · check_accessibility
│   ├── pipeline.py       run_pipeline — ordered steps; returns PipelineResult
│   ├── cli.py            repoguard analyze | fix | gate | serve | mcp  (click entry point)
│   ├── mcp_server.py     8 FastMCP tools (thin wrappers, stdio transport)
│   └── web/
│       ├── __init__.py
│       ├── server.py         FastAPI app: GET / · GET /api/analyze · GET /api/stream (SSE)
│       └── static/index.html Web dashboard
│
├── demo-repo/            Fixture: e-commerce shop with deliberately weak tests
│   ├── pytest.ini
│   ├── shop/
│   │   ├── __init__.py
│   │   ├── api.py            FastAPI routes (8 endpoints)
│   │   ├── cart.py           Cart logic
│   │   ├── inventory.py      Inventory management
│   │   └── pricing.py        Pricing and discount rules
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_api.py       Weak baseline (2 of 8 endpoints covered)
│   │   ├── test_cart.py      Weak baseline
│   │   └── test_pricing.py   Weak baseline
│   └── web/index.html        Shop UI for visual checks
│
├── docs/
│   ├── ARCHITECTURE.md           Layer diagram, data flow, MCP tool list
│   ├── DEMO.md                   3-minute demo script
│   ├── BUILD_WITH_BOB.md         Phase-by-phase build prompts
│   ├── make_results_chart.py     Generates before/after results chart
│   ├── expected-after-tests/     Reference tests — copy in to verify "after" numbers; remove after
│   └── img/                      README badge images
│
├── bob-evidence/         Exported Bob task session reports
├── AGENTS.md             This file — agent context and coding rules
├── RUNBOOK.md            Operational runbook (install, run, troubleshoot)
├── README.md             User-facing overview
├── pyproject.toml        Package metadata and dependencies
├── .gitignore
└── .bobignore
```

## 6. Coding standards
- Type hints on every public function; short docstring saying what it measures and which file it writes.
- Blocking subprocess calls always have a timeout; long-running ones (the app server, `bob run`) are always terminated or awaited. Mutation work copies are deleted after the run.
- No new dependency without saying why in the reply; prefer the standard library.
- No `TODO` comments: implement it or ask.
- Keep functions single-purpose; split a file before it passes ~600 lines.

## 7. Verification (run after any engine change)
Expected results on a clean copy of `demo-repo/` (delete `demo-repo/repoguard-out/` first):

| Check | Command | Expected |
|---|---|---|
| Suite | `cd demo-repo && python3 -m pytest -q` | 5 passed |
| Full measure | `repoguard analyze ./demo-repo` | coverage 65.1%, mutation 20.25% (16/79), 4 files with coverage gaps |
| Determinism | run `run_mutation` twice | identical results (20.25%, 16/79 both times) |
| Visual | run `visual_check` twice with no changes | 0.0% diff |
| After (reference) | copy `docs/expected-after-tests/*.py` into `demo-repo/tests/`, re-measure | TBD — re-measure after reference tests are validated |

Never leave the reference tests inside `demo-repo/tests/` after verifying.

## 8. Ask before doing
- Editing anything under `demo-repo/shop/` or `demo-repo/web/` (it changes every documented number).
- Renaming or removing an MCP tool or a mode slug (breaks the Bob modes and the docs).
- Changing the mutation operators or the visual diff threshold (0.1%) — re-measure and update the docs in the same change.
- Changing the published numbers in README/docs without a real measurement behind them.
When declining an action, say what to do instead.

## 9. Known pitfalls
- **Flaky mutation score:** almost always stale bytecode — confirm `PYTHONDONTWRITEBYTECODE=1` reaches every pytest subprocess.
- **MCP not visible in Bob:** `repoguard` isn't on Bob's PATH; use the absolute path in `.bob/mcp.json`.
- **Visual diffs with no change:** page not fully loaded or animations running.
- **`repoguard fix` fails:** Bob Shell syntax (`bob run --mode repoguard -f stream-json`) is unverified; check `bob run --help` and adjust one line in `pipeline.py`.
- **Equivalent mutants** (e.g. `round(x, 2)` → `round(x, 3)`) can't be killed; report them, don't write artificial tests.

## 10. Token budget
- Reply briefly: tables and lists, no restating tool output.
- Don't read `repoguard-out/*.json`, images or `docs/expected-after-tests/` unless the task needs it.
- Read only the part of a file you need; don't re-read files you just wrote.
- At most 3 subagents per round; pass each one only its file and its data, not the conversation history.

## 11. Git and workflow
- One branch per phase of `docs/BUILD_WITH_BOB.md` (`feat/03-mutation`, `feat/07-mcp-server`, …); never commit to `main`.
- Before opening a PR, run `python3 scripts/verify.py <phase-check>` and paste its output in the PR description; do not open the PR if it FAILs.
- If a PR changes a measured number, update `README.md` / `docs/ARCHITECTURE.md` / `docs/DEMO.md` in the same PR — a number in the docs must always match what `verify.py` just measured.
- Conventional Commits: `feat(engine): …`, `fix(api): …`, `docs(runbook): …`.
- Before committing an engine change, run the Section 7 checks.
- Export the Bob task session report of each meaningful task to `bob-evidence/NN-short-name.md`.
- Update `LASTCONTEXT.md` and `PENDING.md` at the end of every meaningful session.