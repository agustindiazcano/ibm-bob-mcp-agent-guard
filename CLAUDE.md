> **Read `LASTCONTEXT.md` and `PENDING.md` at the start of every session.**
>
> **`AGENTS.md` and `CLAUDE.md` must stay identical.** Different tools read
> different filenames by convention (Claude Code reads `CLAUDE.md`; other
> agents, including Bob, read `AGENTS.md`) — both need the same content, or
> whichever one a given session happens to read goes stale. Edit both in the
> same change, every time.

# Project Context: TestMind AI

## 1. Role
You are a senior Python engineer and QA specialist. You write small, typed, testable code and you never claim a result you did not measure.

## 2. What this project is
TestMind AI measures whether a Python repo's tests actually catch bugs, then uses an AI provider to write the missing tests.
- **Engine** (`repoguard_engine/`, CLI `repoguard`): deterministic measurements — pytest, coverage, AST mutation testing, untested functions, FastAPI endpoint checks, visual regression, risk score, HTML dashboard.
- **AI provider layer** (`repoguard_engine/ai_providers/`): a `ChatProvider` abstraction behind `get_provider()` (`REPOGUARD_AI_PROVIDER`, default `watsonx`, or `--provider` per call). Both `watsonx.py` and `vertex.py` (Google Vertex AI / Gemini) are implemented and live-verified — see `docs/MULTICLOUD_AI.md`.
- **`watson_agent/` fix loop**: a tool-calling fix loop (`repoguard fix`) that writes tests through one hard-guarded tool restricted to `tests/`, calling whichever provider `ai_providers.get_provider()` returns. `narrative.py`'s advisory-only prose summary (`--summarize`) does the same.
- **Entry points:** terminal (`repoguard analyze | fix | gate | serve | mcp`), web UI (`repoguard serve`), any MCP client (stdio).
- The product name is TestMind AI; the CLI, package and MCP server are still named `repoguard`.

> **IBM Bob is retired.** This project used to be built and demoed on IBM
> Bob (`.bob/`: custom modes, hooks, rules, skills). Bob is no longer
> available. `.bob/` is left on disk untouched for historical reference (see
> `.bob/DEPRECATED.md`) but nothing runs it and nothing in
> `repoguard_engine/` depends on it. Claude now authors all code changes, and
> `repoguard_engine/watson_agent/` is the live replacement for what
> `.bob/custom_modes.yaml`'s Orchestrator/Test Writer/Critic/Gate/Publisher
> modes used to do.

## 3. Tech stack
Python ≥ 3.10 · pytest · coverage.py · stdlib `ast` (own mutation engine, no mutmut/Stryker) · MCP Python SDK (FastMCP, stdio) · FastAPI + uvicorn + SSE (web UI) · httpx TestClient (API checks) · Playwright Chromium + Pillow + axe-playwright-python (visual) · matplotlib (docs chart only) · IBM watsonx.ai (`ibm-watsonx-ai`, optional `[ai]` extra) as the default AI provider behind `ai_providers/get_provider()`, used for two things: `narrative.py`'s advisory prose summary (no metric ever comes from it) and `watson_agent/`'s tool-calling fix loop (writes tests through a guarded tool, never a source file).

> **Multicloud AI: both providers built and live-verified.**
> `repoguard_engine/ai_providers/` implements the `ChatProvider` abstraction
> (`base.py`, `watsonx.py`, `vertex.py`) behind `get_provider()`;
> `narrative.py` and `watson_agent/orchestrator.py` both call it instead of
> importing a cloud SDK directly. See `docs/MULTICLOUD_AI.md` /
> `docs/VERTEX_SETUP.md` (Phase 16 in `PENDING.md`) for what was actually
> verified live, including a real Vertex text call and a full tool-calling
> round trip against a real GCP project. A benchmark script comparing
> models by real mutation-score deltas is still deferred (Phase 16 step 4).

## 4. Architecture rules (non-negotiable)
- **The AI decides, the engine measures.** Every number (coverage, mutation score, risk, endpoints, visual diff) must come from an engine function. Never estimate, round up or extrapolate a metric.
- **Source code is the reference.** Agents that write tests may only edit `tests/`. If a new test fails against the original code, the test is wrong unless there is evidence of a real bug; mark that as `xfail(reason="possible bug: ...")`, never fix source to make a test pass.
- **Determinism.** Same repo in, same numbers out. Mutation runs use `PYTHONDONTWRITEBYTECODE=1`; visual checks disable animations and wait for `networkidle`. Any change that makes two identical runs differ is a bug.
- **Layering.** `core.py` has no web, MCP or CLI code. `api_check.py` and `visual.py` depend only on `core`. `pipeline.py` orders the steps. `cli.py`, `mcp_server.py` and `web/server.py` are thin adapters over `pipeline`/`core`.
- **Outputs.** Engine functions return a dict and write `repoguard-out/<name>.json` in the target repo. That folder is the contract between agents: subagents don't share memory, so they communicate through these files.
- **Compact MCP responses.** MCP tools return summaries by default and full data only with `detail=True`. Every response stays in the calling agent's context and is resent each turn; don't add fields to the compact output without a reason.
- **Never print to stdout in the MCP server.** stdio is the protocol channel; stray output corrupts it. Use stderr or return values.

## 5. Directory layout
```
ibm-bob-mcp-agent-guard/
├── .bob/                              RETIRED — see .bob/DEPRECATED.md; left on disk, nothing depends on it
│
├── .github/
│   └── workflows/
│       ├── ci.yml            backend CI: phase0/phase7 verify, demo-repo pytest, gate, mutation determinism — paths-ignore: web-next/**
│       ├── cd.yml            backend CD: build/push image, deploy to Cloud Run — paths-ignore: web-next/**
│       ├── frontend-ci.yml   frontend CI: npm lint + build — paths: web-next/** only
│       └── infra-ci.yml      infra CI: terraform fmt -check + validate, no credentials — paths: infra/terraform/** only
│
├── infra/
│   └── terraform/        Codifies Phase 13's WIF identity (Artifact Registry, deployer SA + roles, WIF pool/provider) — README.md has the terraform import steps; state is local and gitignored
│
├── repoguard_engine/
│   ├── __init__.py
│   ├── core.py           measure_coverage · find_coverage_gaps · run_mutation · compute_risk · build_dashboard_data
│   ├── api_check.py      find_untested_endpoints (AST) · run_endpoint_smoke_tests (httpx)
│   ├── visual.py         capture_screenshot · pixel_diff · collect_console_logs · check_accessibility
│   ├── narrative.py      generate_summary — AI prose from an already-measured dashboard, never a metric source
│   ├── ai_providers/     ChatProvider abstraction — get_provider() reads REPOGUARD_AI_PROVIDER
│   │   ├── base.py           ChatProvider protocol, AIProviderError
│   │   ├── watsonx.py         watsonx.ai chat (tool-calling), fails loud with no credentials — done
│   │   └── vertex.py          Google Vertex AI (google-genai, Gemini) — implemented, live-verified
│   ├── watson_agent/     AI fix loop — replaces .bob/'s Orchestrator/Test Writer/Critic/Gate/Publisher modes
│   │   ├── tools.py          TOOL_SCHEMAS/TOOL_REGISTRY — write_test_file hard-guards writes to tests/ only
│   │   ├── prompts.py        TEST_WRITER_PROMPT, CRITIC_PROMPT — carried forward from .bob/rules,skills
│   │   └── orchestrator.py   run_fix_loop — measure → write → critique → re-measure → evidence
│   ├── pipeline.py       run_pipeline — ordered steps; returns PipelineResult
│   ├── cli.py            repoguard analyze | fix | gate | serve | mcp  (click entry point)
│   ├── mcp_server.py     9 FastMCP tools (thin wrappers, stdio transport)
│   └── web/
│       ├── __init__.py
│       ├── server.py         FastAPI app: GET / · GET /api/analyze · GET /api/stream (SSE) · POST /api/summary · POST /api/fix
│       ├── fix_job.py        Autofix over HTTP: token gate, one-run lock, sandbox copy, NDJSON event stream
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
├── web-next/             Next.js dashboard (Phase 14) — calls the existing FastAPI backend, doesn't replace it
│   ├── app/
│   │   ├── components/       RepoForm · ActionBar · StreamLog · StatCards · GapsList · RiskTable · EndpointsList · SummaryPanel · FixResultPanel
│   │   ├── lib/               api.ts (fetchAnalyze, fetchSummary, streamUrl, streamFix) · types.ts
│   │   └── page.tsx
│   └── package.json
│
├── docs/
│   ├── ARCHITECTURE.md           Layer diagram, data flow, MCP tool list
│   ├── DEMO.md                   3-minute demo script
│   ├── WATSONX_SETUP.md          IBM Cloud credentials for the default AI provider
│   ├── MULTICLOUD_AI.md          ChatProvider abstraction + Vertex AI — both built, see docs/VERTEX_SETUP.md
│   ├── VERTEX_SETUP.md           Google Cloud credentials for the Vertex AI provider
│   ├── AI_ASSISTED_DEVELOPMENT_FRAMEWORK.md  How this repo itself is built
│   ├── make_results_chart.py     Generates before/after results chart
│   ├── expected-after-tests/     Reference tests — copy in to verify "after" numbers; remove after
│   └── img/                      README badge images
│
├── bob-evidence/         RETIRED — old Bob session-report template, never actually populated
├── AGENTS.md             This file — agent context and coding rules (kept byte-identical to CLAUDE.md)
├── RUNBOOK.md            Operational runbook (install, run, troubleshoot)
├── README.md             User-facing overview
├── pyproject.toml        Package metadata and dependencies
├── .gitignore
└── .bobignore
```

## 6. Coding standards
- Type hints on every public function; short docstring saying what it measures and which file it writes.
- Blocking subprocess calls always have a timeout; long-running ones (the app server, the fix loop's `git`/`gh` calls in `watson_agent/orchestrator.py`) are always terminated or awaited. Mutation work copies are deleted after the run.
- No new dependency without saying why in the reply; prefer the standard library.
- No `TODO` comments: implement it or ask.
- Keep functions single-purpose; split a file before it passes ~600 lines.

## 7. Verification (run after any engine change)
Expected results on a clean copy of `demo-repo/` (delete `demo-repo/repoguard-out/` first):

| Check | Command | Expected |
|---|---|---|
| Suite | `cd demo-repo && python3 -m pytest -q` | 5 passed |
| Full measure | `repoguard analyze ./demo-repo --mutation` | coverage 65.1%, mutation 20.25% (16/79), 4 files with coverage gaps (without `--mutation`, mutation is not run and reports `null`) |
| Determinism | run `run_mutation` twice | identical results (20.25%, 16/79 both times) |
| Visual | run `visual_check` twice with no changes | 0.0% diff |
| After (reference) | copy `docs/expected-after-tests/*.py` into `demo-repo/tests/`, re-measure | 71 passed, coverage 100%, mutation 89.87% (71/79) |

Never leave the reference tests inside `demo-repo/tests/` after verifying.

## 8. Ask before doing
- Editing anything under `demo-repo/shop/` or `demo-repo/web/` (it changes every documented number).
- Renaming or removing an MCP tool, or changing `watson_agent/tools.py`'s write guard (the one thing standing between the fix loop and a source-file edit).
- Changing the mutation operators or the visual diff threshold (0.1%) — re-measure and update the docs in the same change.
- Changing the published numbers in README/docs without a real measurement behind them.
When declining an action, say what to do instead.

## 9. Known pitfalls
- **Flaky mutation score:** almost always stale bytecode — confirm `PYTHONDONTWRITEBYTECODE=1` reaches every pytest subprocess.
- **MCP not visible in a client:** `repoguard` isn't on that client's PATH; use the absolute path in its MCP server config (this is what `.bob/mcp.json` used to do for Bob).
- **Visual diffs with no change:** page not fully loaded or animations running.
- **`repoguard fix` fails immediately with a credentials error:** expected behavior with no credentials set for the selected provider (default watsonx: `WATSONX_APIKEY`/`WATSONX_PROJECT_ID`) — see `docs/WATSONX_SETUP.md`. `ai_providers.get_provider()` is called before the baseline measurement runs specifically so this fails in milliseconds, not after several minutes of mutation testing that would've been thrown away anyway.
- **Equivalent mutants** (e.g. `round(x, 2)` → `round(x, 3)`) can't be killed; report them, don't write artificial tests.
- **`run_mutation` MCP tool times out:** a full run on demo-repo's 79 mutants takes several minutes; whatever MCP client config launches `repoguard mcp` needs a `timeout` of at least 600000ms to cover that. If it's ever dropped back toward the default, mutation calls through MCP fail even though the same command works fine from the CLI.
- **FastAPI/starlette mismatch:** `fastapi` and `starlette` are pinned exactly (not `>=`) because they were previously unpinned and different environments resolved to incompatible pairs — one install got a working `fastapi 0.141.1`/`starlette 1.7.0`, another got a broken `fastapi 0.128.0` with that same `starlette 1.7.0`. If a dependency upgrade ever bumps one without the other (e.g. upgrading `fastmcp`/`mcp`, which also depends on `starlette`), reinstall from a clean venv rather than patching the mismatched pair in place.
- **Never call `subprocess.run(["pytest", ...])` or `["python", ...])` with a bare command name.** It resolves via the *caller's ambient PATH*, not the environment `repoguard` is actually installed in — if something else (a stale system Python, an old venv) is earlier on PATH, the subprocess silently runs against a completely different, possibly dependency-less environment. This produced two real, previously undiscovered bugs in one session: (1) `measure_coverage()` fell back to a fabricated `0%`/`0`/`0` result instead of erroring when pytest-cov wasn't on the resolved PATH — silently indistinguishable from a real empty repo; (2) `scripts/verify.py`'s `phase3` check reported a false **PASS** with mutation score **100% (79/79 killed)** — internally consistent across two runs (both hit the same broken interpreter, so "deterministic"), but the number was completely wrong, because pytest itself couldn't run in every single mutant subprocess and every one was scored "killed" by default. Both are fixed by always using `sys.executable` (or `[sys.executable, "-m", "pytest", ...]`), which pins the subprocess to the exact interpreter already running the code, regardless of ambient PATH. The one deliberate exception is `verify.py`'s `phase0` check, which uses bare `repoguard` on purpose — it's specifically testing whether the console script is on PATH, the same way `.bob/mcp.json` used to invoke it for Bob (see `.bob/DEPRECATED.md`) and any current MCP client config does today.
- **A script reporting PASS is not proof it measured the real thing** — `phase3`'s determinism check alone (do two runs agree?) let the 100%-false-positive above slip through, because two runs of the *same broken environment* agree with each other trivially. `phase3` now also asserts against the documented `AGENTS.md §7` baseline (`killed == 16`, `total == 79`) as a second, independent check — internal consistency and a known-good external value, not just internal consistency alone.
- **`check_accessibility()` silently reported "0 violations" (a fake clean pass) instead of failing** when `axe-playwright-python` wasn't installed — it was imported in `visual.py` but never declared as a dependency anywhere, so the check has likely never actually run in any environment. Now declared as a dependency, and the function returns `ok=False` with a real `error` message (surfaced through the MCP tool's compact response) whenever the check couldn't actually run, instead of an empty result that looks identical to a genuine pass.
- **`narrative.py` needs `pip install -e ".[ai]"` plus credentials for the selected provider** (default watsonx: `WATSONX_APIKEY`/`WATSONX_PROJECT_ID`) — see `docs/WATSONX_SETUP.md`. Without them, `generate_summary()` returns `ok=False` with a real error, same graceful-degradation pattern as `check_accessibility()` — it never fabricates summary text. Its output is advisory prose only; no code path may read a number out of it back into a measurement. **Live-verified with real watsonx.ai credentials**: a real `--summarize` call returns real generated text (first confirmed successful generation, not just a clean-failure network check).
- **`watson_agent/`'s fix loop degrades differently from `narrative.py`: it fails loud, not gracefully.** `ai_providers.get_provider()` raises `AIProviderError` (a `WatsonxCredentialsError`/`VertexCredentialsError` subclass) rather than returning an `ok=False` result — `repoguard fix` has no measurement to fall back to if the AI stage can't run, unlike `--summarize`'s advisory text. `ModelInference.chat()`'s signature and OpenAI-compatible response shape (`response["choices"][0]["message"]`, `tool_calls`) were confirmed against the real installed `ibm-watsonx-ai==1.7.2` via `inspect.signature()`/`help()` — including that its `params` dict takes `max_tokens`/`time_limit`, not `generate_text()`'s `max_new_tokens` (a real bug this session's refactor fixed: `narrative.py` had been passing the wrong param name). **Live-verified**: a real tool-calling round trip runs end to end against a real IBM Cloud account — but the current default model (`mistral-small-3-1-24b-instruct-2503`, chosen to dodge `llama-3-3-70b-instruct`'s free-tier `429`s) doesn't reliably invoke tools; a real `repoguard fix demo-repo` run produced zero mutation-score improvement because the critic replied in plain text instead of calling `read_source_file`. This is a model-choice quality gap, not a call-shape bug — motivating Vertex AI (Phase 16 Stage B) as a more reliable provider. `scripts/verify.py phase16`/`multicloud` check the write guard and fail-loud path, not model quality.
- **`ai_providers/orchestrator.py`'s tool dispatch only caught `SourceEditRejected`, so any other tool failure (a hallucinated file path, bad args) crashed the whole fix loop.** Found live: a real Vertex AI (Gemini) run's critic stage called `read_source_file` on a path that didn't exist, raising a raw `FileNotFoundError` that propagated out of `run_fix_loop()` entirely. Fixed by catching any `Exception` around each tool call (not just the write guard) and reporting it back to the model as a normal `{"error": ...}` tool result, same as a `SourceEditRejected` — a bad tool call is something the model should see and adapt to, not a reason to crash the host process.
- **A second, more serious false-100%-mutation-score bug, structurally identical to the `phase3` one above but with a different root cause.** The same Vertex/Gemini run then reported mutation score **100% (79/79 killed)** — before this was investigated, that would have been reported as a real success. It wasn't: `_run_mutant()` scores a mutant "killed" whenever pytest exits non-zero on the *mutated* copy, but nothing ever checked that pytest exits **zero on the unmutated baseline first** — Gemini's newly written `tests/test_shop_api.py` had 10 real failures against the original, unmutated `shop/` code, so every single mutant run inherited those failures and scored "killed" trivially, regardless of whether the mutation itself was ever exercised. `run_mutation()` now runs the unmutated suite once before mutating anything and raises `RuntimeError` (same pattern as `measure_coverage()`'s missing-`coverage.json` check) if it doesn't pass — confirmed this correctly refuses on the broken suite instead of reporting 100%, and confirmed the documented `AGENTS.md §7` baseline (20.25%, 16/79) is unaffected on a clean suite. This is exactly the kind of result an AI-written test suite can produce (tests that don't even pass against real code) and now can't silently masquerade as a perfect score.
- **Autofix (`POST /api/fix`) returns `503`:** expected when `REPOGUARD_FIX_TOKEN` isn't set on the server. The endpoint is off by default because each run spends AI-provider quota for minutes on a public service; on Cloud Run the token is a Secret Manager secret attached by hand (`docs/DEPLOY.md` §5). A wrong or missing bearer token gets `401`, and a second concurrent run gets `409`.
- **Autofix never touches the target repo.** `web/fix_job.py` copies the repo to a temp dir, runs `run_fix_loop(..., publish=False)` there, returns the written tests in the final `done` event and deletes the copy. Don't "simplify" it into running in place: on Cloud Run that would rewrite the bundled `demo-repo/tests/` that every documented baseline number depends on. `verify.py phase14fix` asserts `demo-repo/` stays byte-identical.

## 10. Token budget
- Reply briefly: tables and lists, no restating tool output.
- Don't read `repoguard-out/*.json`, images or `docs/expected-after-tests/` unless the task needs it.
- Read only the part of a file you need; don't re-read files you just wrote.
- At most 3 subagents per round; pass each one only its file and its data, not the conversation history.

## 11. Git and workflow
- One branch per phase in `PENDING.md` (`feat/03-mutation`, `feat/15-watsonx-migration`, …); never commit to `main`.
- Before opening a PR, run `python3 scripts/verify.py <phase-check>` and paste its output in the PR description; do not open the PR if it FAILs.
- If a PR changes a measured number, update `README.md` / `docs/ARCHITECTURE.md` / `docs/DEMO.md` in the same PR — a number in the docs must always match what `verify.py` just measured.
- Conventional Commits: `feat(engine): …`, `fix(api): …`, `docs(runbook): …`.
- Before committing an engine change, run the Section 7 checks.
- `repoguard fix` writes its own run report automatically to `<target-repo>/watson-evidence/NN-fix-loop.md` — no manual export step. (`bob-evidence/` at this project's root is retired, see `.bob/DEPRECATED.md`.)
- Update `LASTCONTEXT.md` and `PENDING.md` at the end of every meaningful session.
