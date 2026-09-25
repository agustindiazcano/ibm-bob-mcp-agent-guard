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

> **Session note (since Session 6):** Bob's remaining credits are reserved for
> *running* the application (measurement, the live demo, `repoguard serve`) —
> not for authoring new code. Until that changes, code changes (engine,
> Docker, CI/CD, the reference tests) are written by Claude, not by Bob's
> Test Writer/Fixer subagents. The `.bob/custom_modes.yaml` pipeline and its
> rules still describe the intended design and stay unchanged — they're what
> Bob runs once credits allow, and what the live demo still shows executing.
> This note goes away once Bob is authoring code again.

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
│       ├── pytest-conventions/SKILL.md   Fixture, parametrize, conftest conventions
│       ├── test-writer/SKILL.md          Step-by-step guide for writing mutant-killing tests
│       └── verify-before-pr/SKILL.md    Gate check before opening a PR
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
│   │   ├── api.py            FastAPI routes (7 endpoints)
│   │   ├── cart.py           Cart logic
│   │   ├── inventory.py      Inventory management
│   │   └── pricing.py        Pricing and discount rules
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_api.py       Weak baseline (1 of 7 endpoints covered)
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
| After (reference) | copy `docs/expected-after-tests/*.py` into `demo-repo/tests/`, re-measure | 71 passed, coverage 100%, mutation 89.87% (71/79) |

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
- **`run_mutation` MCP tool times out:** a full run on demo-repo's 79 mutants takes several minutes; `.bob/mcp.json`'s `timeout` (600000ms) has to cover that. If it's ever dropped back toward the default, mutation calls through MCP fail even though the same command works fine from the CLI.
- **FastAPI/starlette mismatch:** `fastapi` and `starlette` are pinned exactly (not `>=`) because they were previously unpinned and different environments resolved to incompatible pairs — one install got a working `fastapi 0.141.1`/`starlette 1.7.0`, another got a broken `fastapi 0.128.0` with that same `starlette 1.7.0`. If a dependency upgrade ever bumps one without the other (e.g. upgrading `fastmcp`/`mcp`, which also depends on `starlette`), reinstall from a clean venv rather than patching the mismatched pair in place.
- **Never call `subprocess.run(["pytest", ...])` or `["python", ...])` with a bare command name.** It resolves via the *caller's ambient PATH*, not the environment `repoguard` is actually installed in — if something else (a stale system Python, an old venv) is earlier on PATH, the subprocess silently runs against a completely different, possibly dependency-less environment. This produced two real, previously undiscovered bugs in one session: (1) `measure_coverage()` fell back to a fabricated `0%`/`0`/`0` result instead of erroring when pytest-cov wasn't on the resolved PATH — silently indistinguishable from a real empty repo; (2) `scripts/verify.py`'s `phase3` check reported a false **PASS** with mutation score **100% (79/79 killed)** — internally consistent across two runs (both hit the same broken interpreter, so "deterministic"), but the number was completely wrong, because pytest itself couldn't run in every single mutant subprocess and every one was scored "killed" by default. Both are fixed by always using `sys.executable` (or `[sys.executable, "-m", "pytest", ...]`), which pins the subprocess to the exact interpreter already running the code, regardless of ambient PATH. The one deliberate exception is `verify.py`'s `phase0` check, which uses bare `repoguard` on purpose — it's specifically testing whether the console script is on PATH, the same way `.bob/mcp.json` invokes it.
- **A script reporting PASS is not proof it measured the real thing** — `phase3`'s determinism check alone (do two runs agree?) let the 100%-false-positive above slip through, because two runs of the *same broken environment* agree with each other trivially. `phase3` now also asserts against the documented `AGENTS.md §7` baseline (`killed == 16`, `total == 79`) as a second, independent check — internal consistency and a known-good external value, not just internal consistency alone.
- **`check_accessibility()` silently reported "0 violations" (a fake clean pass) instead of failing** when `axe-playwright-python` wasn't installed — it was imported in `visual.py` but never declared as a dependency anywhere, so the check has likely never actually run in any environment. Now declared as a dependency, and the function returns `ok=False` with a real `error` message (surfaced through the MCP tool's compact response) whenever the check couldn't actually run, instead of an empty result that looks identical to a genuine pass.

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