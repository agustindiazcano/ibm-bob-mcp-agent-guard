[![AI: Vertex AI | watsonx.ai](https://img.shields.io/badge/AI-Vertex%20AI%20%7C%20watsonx.ai-0f62fe?style=for-the-badge)](docs/MULTICLOUD_AI.md)
[![MCP server](https://img.shields.io/badge/Protocol-MCP-4a4a4a?style=for-the-badge)](https://modelcontextprotocol.io/)
[![Python | FastAPI](https://img.shields.io/badge/Engine-Python%20%7C%20FastAPI-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)

# TestMind AI

**A test-quality tool that proves whether your tests catch bugs, then runs AI agents (a test writer and a critic, sequentially or as a parallel swarm) to write the ones that are missing, on Google Vertex AI (Gemini) or IBM watsonx.ai. Its measurement engine is also an MCP server, so any MCP-capable AI agent can drive it.**

> Coverage tells you which lines ran. It doesn't tell you whether your tests would notice a bug.
> TestMind AI injects bugs into your code on purpose and measures how many your tests catch.

## At a glance

TestMind AI is not a chat UI over a model API. The AI only ever writes test
files, through a tool that can't write outside `tests/`. Every number it
reports (coverage, mutation score, risk, endpoints, the quality gate) comes
from a deterministic engine built for this project. Replace the model with a
scripted, credential-free stand-in, and the engine still measures exactly the
same way. That is how CI verifies the whole loop without any AI credentials.

| Layer | What's built |
|---|---|
| **Measurement engine** | Own mutation-testing engine on Python's `ast` (no mutmut/Stryker): parallel workers, stable per-mutant fingerprints, a sham-mutant control, and a refusal to score when the unmutated suite is red. Plus coverage on source only, gap and risk analysis, FastAPI endpoint checks, and Playwright visual/accessibility checks |
| **AI agents** | A sequential writer → critic fix loop, and a multi-agent swarm (`--swarm`): one lane per file in its own sandbox, a read-only critic with a JSON verdict, fan-in with stability checks and rollback, one global Gate |
| **Guardrails** | Env allow-list, AST policy against cheating tests, 3× acceptance runs with a canary, explicit killed/survived/timeout/error outcomes, and a held-out second fixture (`eval-fixtures/ledger/`) |
| **Multicloud AI** | One `ChatProvider` abstraction over Google Vertex AI (Gemini, the default) and IBM watsonx.ai, both live-verified; the writer and critic can run on different providers |
| **Interfaces** | CLI, MCP server (9 tools, stdio), FastAPI with SSE/NDJSON streaming, and a Next.js dashboard with run history |
| **Data** | Run history on SQLAlchemy Core (SQLite or Postgres 16 on Cloud SQL), with derived trends in SQL views and per-project ingest tokens |
| **Infra** | Cloud Run (backend) and Vercel (frontend), Terraform, Workload Identity Federation (no service-account keys), rate limiting and a per-IP run lock that hold across Cloud Run instances, and GitHub Actions CI/CD for backend, frontend and infra |
| **Verification** | 30 `scripts/verify.py` checks; the measurement ones are pinned to measured reference values (`AGENTS.md §7`), not just to two runs agreeing with each other |

**Size** (tracked files, measured with `git ls-files | wc -l`, excluding
lockfiles, JSON and images): about 7.4k lines of Python in the engine, 3.0k in
the verification scripts, 9.7k of TypeScript/CSS in the frontend, 0.7k of
Terraform and CI YAML, and 11k lines of documentation.

**Naming.** *TestMind AI* is the product. **`repoguard` is its engine**: the
Python package (`repoguard_engine/`), the CLI (`repoguard analyze | fix | gate
| serve | mcp`), the MCP server, and the output folder (`repoguard-out/`).
The engine name predates the product name and was kept on purpose, so CLI
commands, MCP client configs and CI pipelines didn't break when the product
was renamed.

## Table of Contents

- [At a glance](#at-a-glance)
- [Results on the bundled demo repo](#results-on-the-bundled-demo-repo)
- [What it does](#what-it-does)
- [How it works](#how-it-works)
- [Is it multi-agent?](#is-it-multi-agent)
- [Multi-agent swarm](#multi-agent-swarm)
- [Evaluation & guardrails](#evaluation--guardrails)
- [Quick start](#quick-start)
- [Commands](#commands)
- [Using the AI fix loop](#using-the-ai-fix-loop)
- [Requirements](#requirements)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [CI/CD](#cicd)
- [Deploy to Google Cloud](#deploy-to-google-cloud)
- [Database](#database)
- [Infrastructure as code](#infrastructure-as-code)
- [IBM Bob Usage](#ibm-bob-usage)
- [AI-Assisted Development](#ai-assisted-development)
- [Documentation](#documentation)
- [Roadmap](#roadmap)
- [Limitations](#limitations)

## Results on the bundled demo repo

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/img/results-en-dark.png">
  <img alt="Before numbers on demo-repo, measured with RepoGuard's own AST mutation engine: line coverage 60.3%, bugs caught 20.25%" src="docs/img/results-en-light.png">
</picture>

| demo-repo | Before | After |
|---|---|---|
| Tests | 5 | 71 |
| Line coverage | 60.3% | 100% |
| **Bugs caught (mutation score)** | **20.25%** (16/79) | **89.87%** (71/79) |
| API endpoints with tests | 1 of 7 | 7 of 7 |
| Visual regression | baseline saved | catches a button color change |

The demo's tests covered 60.3% of the lines but caught roughly 1 in 5 injected bugs;
the reference tests in [`docs/expected-after-tests/`](docs/expected-after-tests/) catch
9 in 10. Both measured with RepoGuard's own AST mutation engine (see `AGENTS.md §7`);
the earlier figures on this page came from an interim `mutmut`-based engine and are
superseded. The 8 mutants still surviving after "After" are equivalent mutants, not
gaps: an `is_member` field `api.py` never reads, and `round(x, 2)` precision changes
that don't affect the tested inputs — see `AGENTS.md §9`.

### The same "Before" run in the dashboard

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/img/dashboard-dark.png">
  <img alt="TestMind AI web dashboard after analyzing demo-repo with mutation testing: line coverage 60.3% (91/151 lines), mutation score 20.25% (16/79 mutants killed), 4 files with coverage gaps, quality gate FAIL at an 80% threshold, risk ranking led by shop/inventory.py at 0.54" src="docs/img/dashboard-light.png">
</picture>

A real capture of the [`web-next/`](web-next/) dashboard (deployed at
https://ibm-bob-mcp-agent-guard.vercel.app/) running against a local
`repoguard serve` — every number on it comes straight from the engine. The AI
summary panel shows "unavailable" because no AI credentials were configured
for the capture; that's its normal state without them. How to retake it:
[`docs/img/README.md`](docs/img/README.md).

### The app in Demo Mode

The site has a **Demo** switch (top right) that turns it into a slide deck
and replays an Autofix run without spending AI quota. The timing is simulated,
but the numbers are the measured `AGENTS.md §7` reference run
(20.25% → 89.87% mutation, 60.3% → 100% coverage). Live site:
https://ibm-bob-mcp-agent-guard.vercel.app/

<table>
<tr>
<td width="50%"><img src="docs/img/demo-autofix.png" alt="Autofix replay in Demo Mode: live progress log for writer and critic per file, then mutation score 20.25% (16/79) to 89.87% (71/79) and line coverage 60.3% to 100%, with the generated test files shown in a code viewer"><br/><sub><b>Autofix:</b> live progress, before → after, and the generated tests</sub></td>
<td width="50%"><img src="docs/img/demo-results.png" alt="Results dashboard in Demo Mode for the demo-showcase project: KPI tiles, coverage vs. mutation score per commit, survival by mutation operator, file risk ranking, untested endpoints and persistent survivors"><br/><sub><b>Results:</b> run history, survival by mutation operator, risk, endpoints, and mutants that are never killed</sub></td>
</tr>
<tr>
<td colspan="2" align="center"><img src="docs/img/demo-intro.png" width="70%" alt="TestMind AI intro slide with the Demo switch on"><br/><sub>Intro slide. The numbered tabs 00–10 are the deck</sub></td>
</tr>
</table>

## What it does

- 🧬 **Mutation testing.** Injects one small bug at a time (flipped comparisons, swapped operators, changed constants, `return None`, removed `raise`) with its own AST engine, then reruns your suite. Every mutant that survives is a bug your tests would miss.
- 🧪 **Writes the missing tests.** `repoguard fix` hands each file's surviving mutants to the configured AI provider (Google Vertex AI by default, or IBM watsonx.ai), one file at a time, through a guarded tool that can only write under `tests/` — never source. A second watsonx.ai call critiques the new test before the suite is re-measured for real.
- 🌐 **API checks.** Finds a FastAPI app's routes by parsing its source (AST), flags endpoints no test calls, and smoke-tests `GET` endpoints for 5xx errors.
- 👁️ **Visual regression.** Takes a screenshot of a running page (Playwright/Chromium, any viewport, 1280×720 by default) and diffs it pixel by pixel against a baseline. Also reports console errors and basic accessibility issues. Available as MCP tools, not yet as a CLI command.
- 📊 **Risk ranking and report.** Ranks files by the share of their lines left uncovered (`uncovered lines / non-blank lines`) and builds an HTML dashboard. Extra terms such as git churn are planned only if stored run history shows they predict surviving mutants better — see [`docs/DATA_PLATFORM.md` §5](docs/DATA_PLATFORM.md#5-risk-model-v2--calibrated-not-invented).

**Design principle:** the AI decides what to test, and deterministic tools do the measuring. No number in the report is estimated by a model.

## How it works

One engine, three ways to use it.

```mermaid
flowchart TB
    CLI["Terminal<br/>repoguard analyze · fix · gate"]
    WEB["Web UI<br/>repoguard serve"]
    EXT["Any MCP client<br/>(Claude Code, etc.)"]

    PIPE["Pipeline<br/>step order"]
    MCP["MCP server<br/>9 tools"]
    WATSON["AI fix loop (Vertex AI · watsonx.ai)<br/>repoguard_engine/watson_agent/ · swarm/"]

    MED["Measurements<br/>tests · coverage · mutation · gaps<br/>API · visual · risk"]
    REPO[("Target repo")]
    OUT[("repoguard-out/<br/>JSON · screenshots · dashboard.html")]

    CLI --> PIPE
    CLI -. "fix" .-> WATSON
    WEB -- "HTTP + SSE" --> PIPE
    EXT -- "MCP stdio" --> MCP
    MCP --> MED
    PIPE --> MED
    WATSON -- "writes tests/, then re-measures" --> MED
    MED -- "runs" --> REPO
    MED -- "writes" --> OUT
```

## Is it multi-agent?

**Yes, in two modes.** By default, `repoguard fix` runs two agents in sequence; `repoguard fix --swarm` runs them as a parallel swarm, one lane per file (see [Multi-agent swarm](#multi-agent-swarm)). The default mode runs an orchestrator that, for each of up to 3 files prioritized by risk, runs two agents one after the other:

- **Test writer agent:** its own system prompt, and a tool-calling loop over `read_source_file` and `write_test_file`. The write tool is hard-guarded to `tests/`.
- **Critic agent:** a separate system prompt, with the same guarded tools, reviewing what the writer produced.

After both, the orchestrator re-measures deterministically. Both agents use the same configured AI provider (Google Vertex AI by default, or IBM watsonx.ai), and measurement itself never uses AI.

The engine is also exposed through **MCP** (9 tools), so external agents such as Claude Code or any other MCP client can call the same measurements. The fix loop itself calls the engine directly rather than through MCP.

**What it is not (yet):**
- **The swarm isn't benchmarked with a real model yet.** `--swarm` is built and verified end to end with a scripted, credential-free provider. It hasn't yet been compared against the sequential loop on real Vertex/watsonx runs (speed and final score). See [Multi-agent swarm](#multi-agent-swarm).
- **Multicloud, for real.** The `ChatProvider` abstraction (`repoguard_engine/ai_providers/`) is implemented; both watsonx.ai and Google Vertex AI (Gemini) run through it, `REPOGUARD_AI_PROVIDER`/`--provider` select which — see [`docs/MULTICLOUD_AI.md`](docs/MULTICLOUD_AI.md) (`PENDING.md` Phase 16).

```mermaid
flowchart TB
    B["Baseline measure<br/>(coverage, mutation, risk)"]
    B --> P["Prioritize up to 3 files<br/>by risk score"]
    P --> W["AI writer: write a test<br/>(tests/ only, guarded)"]
    W --> C["AI critic: critique it<br/>(read-only unless it rewrites, tests/ only)"]
    C --> G["Re-measure<br/>(deterministic, no AI)"]
    G -->|"--publish, gate passes"| PR["branch + commit + PR"]
```

| Entry point | Uses AI? | What runs |
|---|---|---|
| `repoguard fix` | Yes | The AI loop above (write → critique → re-measure), or the swarm with `--swarm` |
| `repoguard analyze [--summarize]` | Only with `--summarize` | Deterministic pipeline; `--summarize` adds one AI call for prose, never a metric |
| `repoguard gate` (CI) | No | Deterministic pipeline |

## Multi-agent swarm

> `PENDING.md` Phase 18, Steps S0–S7 **built and verified with no
> credentials**: `repoguard fix --swarm`. Still to do: a real-model benchmark
> against the sequential loop (Step 8), the lanes view in the web UI (S8),
> and a CI job. Full plan: [`docs/MULTI_AGENT_SWARM.md`](docs/MULTI_AGENT_SWARM.md).

```bash
repoguard fix demo-repo --swarm                       # one lane per file, min(lanes, 4) in parallel
repoguard fix demo-repo --swarm --workers 4 --rounds 2 --mutation-workers 4
REPOGUARD_CRITIC_PROVIDER=watsonx repoguard fix demo-repo --swarm --provider vertex   # independent critic
```

The swarm IBM Bob was designed to run (`.bob/custom_modes.yaml`: Orchestrator, Test Writer, Critic, Gate, Publisher…), rebuilt in-process and provider-agnostic (Vertex AI or watsonx.ai). Instead of one loop working file by file, the Orchestrator opens **one lane per source file** and runs the lanes **in parallel**. Each lane has three agents:

- **Test Writer (LLM):** writes tests aimed at that file's surviving mutants, in its own sandbox copy of the repo. It can only write its own test file.
- **Verifier (deterministic):** runs mutation testing on that file and reports which mutants the new tests killed.
- **Critic (LLM, read-only):** has no write tool. It runs the tests and answers with a JSON verdict: `APPROVED`, `NEEDS_WORK` or `BLOCKED`. `NEEDS_WORK` or a red suite triggers one more writer round, with the critic's weaknesses in the prompt. The verdict is advisory: whether a lane is accepted always comes from the Verifier's measurement. The writer and the critic can run on different providers (`REPOGUARD_WRITER_PROVIDER` / `REPOGUARD_CRITIC_PROVIDER`).

After all lanes finish, **fan-in** merges their files one at a time in a separate sandbox. A file that turns the suite red, or makes it flaky (3 forward runs, reversed file order, each file alone), is dropped as `REJECTED_AT_FANIN`. Fan-in also aborts if `tests/` changed during the run. Then the **Gate** re-measures the whole repo once, and that number is the only one reported. If the Gate itself fails, the merge is rolled back byte for byte. The **Publisher** opens a PR if the score improved, and the **Reporter** writes `watson-evidence/NN-swarm.md`. Agents talk through files in `repoguard-out/swarm/<run_id>/`, like Bob's subagents did, so every run is auditable. Mutation testing itself also runs in parallel.

**Measured with no credentials** (`python scripts/verify.py phase18-s7`, where a scripted provider plays the model and every number comes from the engine):

| | Before | Swarm Gate (4 lanes in parallel) |
|---|---|---|
| Tests passed | 5 | 71 |
| Line coverage | 60.3% | 100.0% |
| Mutation score | 20.25% (16/79) | **89.87% (71/79)** |

All 4 lanes were `ACCEPTED`, 6 lane pairs overlapped in time, and `--workers 1` produced the identical Gate with the same 8 surviving mutants. Every sandbox was cleaned up and `demo-repo/` stayed untouched. 71/79 is the ceiling for this fixture; it matches the hand-written reference tests.

| Check | What it proves |
|---|---|
| `phase18-s5` | `NEEDS_WORK` → exactly one more round, with the weakness in the prompt; an unparseable critic doesn't trigger a paid round; the critic can't write |
| `phase18-s6` | Two files that pass alone but fail together → the later one is rejected at fan-in; a failing Gate rolls back |
| `phase18-s7` | The end-to-end numbers above |

The swarm still has to earn its place against the sequential loop on real model runs: it must be faster and reach at least the same final score. Until then, `repoguard fix` keeps the sequential loop as its default.

| Doc section | What it covers |
|---|---|
| [§2](docs/MULTI_AGENT_SWARM.md#2-bob-then-today-target) | Bob's modes mapped one by one to the new agents |
| [§3](docs/MULTI_AGENT_SWARM.md#3-problems-in-todays-loop-the-swarm-must-fix) | Six problems in today's loop the swarm fixes |
| [§5](docs/MULTI_AGENT_SWARM.md#5-parallelism) | Two levels of parallelism, and per-lane isolation |
| [§6](docs/MULTI_AGENT_SWARM.md#6-communication-contract-the-blackboard) | The file contract between agents |
| [§10](docs/MULTI_AGENT_SWARM.md#10-build-order) | Build order and cut line |
| [§11](docs/MULTI_AGENT_SWARM.md#11-verification-scriptsverifypy-phase18) | Verification, including a credential-free end-to-end test |

## Evaluation & guardrails

> **Built and verified in CI (`PENDING.md` Phase 19).** Plan: [`docs/EVAL_GUARDRAILS_PLAN.md`](docs/EVAL_GUARDRAILS_PLAN.md) · build steps: [`docs/EVAL_GUARDRAILS_IMPLEMENTATION.md`](docs/EVAL_GUARDRAILS_IMPLEMENTATION.md).

TestMind AI has integrity guardrails against **LLM hallucinations and
cheating**. A model writing tests can hallucinate trivial assertions, write
tests that pass without checking anything, or cheat by reading source files
or hashing them to inflate the mutation score to 100%.

> **In short:** the full guardrail suite (G1–G6 and O1) is implemented in the
> engine and runs continuously in GitHub Actions (the `guardrails-phase19`
> job), all green.

### Guardrails against LLM hallucinations and cheating

| Guardrail | Hallucination or cheat it blocks | Control | Verified by |
|---|---|---|---|
| **G1: Env allow-list** | Leaking or misusing server secrets (`REPOGUARD_FIX_TOKEN`, `WATSONX_APIKEY`) | Strict allow-list of environment variables in the pytest subprocess; no secret reaches generated code | ✅ **PASS** (`phase19-env` in CI, 40s) |
| **G2: AST policy** | Tests with no `assert`, reading source files (`open('shop/api.py')`), hashing (`hashlib`), pytest hooks, or abusive skips | Static AST analysis before anything is written to disk; rejects any cheating pattern or empty test | ✅ **PASS** (`phase19-policy` in CI, 40s) |
| **G3: Acceptance gate** | Flaky tests, order-dependent tricks, and deleting or vandalizing existing tests | 3 identical runs, a no-op canary in the source, checks that existing test IDs are preserved, and full-suite bisection; failures go to quarantine | ✅ **PASS** (`phase19-accept` in CI, 40s) |
| **G4: Mutation integrity** | Mutants falsely counted as "killed" because the pytest harness crashed or errored | Explicit outcomes (`killed`, `survived`, `timeout`, `error`); harness errors never count as caught bugs | ✅ **PASS** (`engine-parallel-mutation` in CI) |
| **G5: Integrity and status** | False-positive reports; publishing a PR without a real mutation gain | `FixResult.status` (`accepted`, `partial`, `rejected`), an integrity record, and mandatory persisted evidence | ✅ **PASS** (`fix-loop-stub` in CI) |
| **G6: Source-only coverage** | Inflating coverage by counting the test files' own lines (`tests/`) | Coverage measured strictly on production code (`shop/`): 60.2649% (91/151 lines), `tests/` excluded | ✅ **PASS** (`quality-gate` in CI, 30s) |
| **O1: Structured run record** | Lost traceability or hallucinated run reports | Atomic `repoguard-out/fix_run.json` recording every tool call and decision | ✅ **PASS** (`fix-loop-stub` in CI) |
| **E2: Fix-loop evaluation** | Unreproducible, biased evaluation of AI models | Repeated benchmark (`scripts/eval_fixloop.py`, K=3): ΔMS, gaps closed, validity, and min/median/max violations | 🟡 Ready; needs real-model credentials |
| **E3: Held-out fixture** | Overfitting to demo-repo's domain (e-commerce) | Separate fixture `eval-fixtures/ledger/` (accounting ledger). Baseline: 52.17% coverage, 19.18% mutation (14/73); ceiling: 100% coverage, 69.86% mutation (51/73) | ✅ **PASS** (`phase19-e3` in CI) |

### CI test suite (GitHub Actions)

| CI job | What it checks | Result | Time |
|---|---|---|---|
| **`quality-gate`** | Phase 0 skeleton, Phase 7 compact MCP, `demo-repo` pytest, 60.0% coverage gate | ✅ **PASS** | 30s |
| **`guardrails-phase19`** | G1 (`phase19-env`), G2 (`phase19-policy`), G3 (`phase19-accept`), E3 (`phase19-e3` ledger) | ✅ **PASS** | 3m 0s |
| **`mutation-determinism`** | Phase 3 AST mutation determinism (two identical runs over 79 mutants) | ✅ **PASS** | 2m 5s |
| **`store`** | Phase 17: SQLite + real PostgreSQL 16, endpoints, mutants/tests tables, history routes | ✅ **PASS** | 4m 36s |
| **`fix-loop-stub`** | Phase 18 S0: sequential loop with `ScriptedProvider`, tools and evidence | ✅ **PASS** | 3m 6s |
| **`engine-parallel-mutation`** | Phase 18 S1 parallel workers, single-file scope, Phase 17/18 per-mutant records | ✅ **PASS** | 2m 41s |
| **`swarm-phase18`** | Phase 18 S4: swarm lane state machine, thread pool, blackboard, multi-agent runner | ✅ **PASS** | 4m 16s |
| **`frontend-ci`** | Lint and production build of the Next.js app (`web-next`) | ✅ **PASS** | 26s |

## Quick start

```bash
pip install -e .                    # installs the `repoguard` command
playwright install chromium         # only needed for visual checks

repoguard analyze ./demo-repo --mutation   # coverage, gaps, risk + mutation score (slow)
repoguard serve                     # web UI at http://127.0.0.1:8765
```

## Commands

| Command | What it does |
|---|---|
| `repoguard analyze <path> [--mutation] [--endpoints] [--summarize]` | Runs the tests and measures coverage, gaps and risk. `--mutation` adds the mutation score (slow), and `--endpoints` flags untested FastAPI endpoints. No AI unless `--summarize` is passed. Visual checks are MCP tools only. |
| `repoguard fix <path> [--publish] [--threshold N] [--provider vertex\|watsonx]` | Measures, has the AI write the missing tests (guarded to `tests/`), critiques them, measures again |
| `repoguard fix <path> --swarm [--workers N] [--rounds 2] [--mutation-workers M]` | Same, as a parallel swarm: one writer/critic lane per file in its own sandbox, fan-in, one global Gate |
| `repoguard gate <path> --threshold 80` | CI gate: exits with code 1 if coverage is below the threshold |
| `repoguard serve [--port 8000]` | Web UI with live progress, metrics and the report |
| `repoguard mcp` | Starts the MCP server (9 tools) for any MCP client |

## Using the AI fix loop

TestMind AI is multicloud: the fix loop and the advisory summary run against
whichever provider `REPOGUARD_AI_PROVIDER` selects (`vertex`, the default,
or `watsonx`), or per call via `--provider` — see
[`docs/MULTICLOUD_AI.md`](docs/MULTICLOUD_AI.md). Both are built and
live-verified. For Vertex AI (Gemini, default model `gemini-3.8-flash`),
install `pip install -e ".[vertex]"` and follow
[`docs/VERTEX_SETUP.md`](docs/VERTEX_SETUP.md). The steps below are for
watsonx.ai.

1. Get IBM Cloud credentials and install the optional extra — see [`docs/WATSONX_SETUP.md`](docs/WATSONX_SETUP.md):
   ```bash
   pip install -e ".[ai]"
   export WATSONX_APIKEY="<your IBM Cloud API key>"
   export WATSONX_PROJECT_ID="<your watsonx project id>"
   ```
2. Run it:
   ```bash
   repoguard fix demo-repo
   repoguard fix demo-repo --provider watsonx   # equivalent, explicit
   ```
3. Without credentials, `fix` fails immediately with a clear error — it never
   silently skips the AI stages or fabricates a result.

`repoguard_engine/ai_providers/` holds the provider abstraction
(`base.py`'s `ChatProvider` protocol, `watsonx.py` and `vertex.py`
implementations) behind `get_provider()`.
`repoguard_engine/watson_agent/` is the rest of the fix loop: `tools.py` (the
one write tool, hard-guarded to `tests/`), `prompts.py` (the writer/critic
system prompts), and `orchestrator.py` (the loop itself, provider-agnostic).
It calls `pipeline`/`core` directly, the same way `web/server.py` does — no
MCP round-trip needed for its own use.

## Requirements

| Dependency | Used for | Required |
|---|---|---|
| Python ≥ 3.10, pytest, coverage | Running and measuring the suite | Yes |
| fastmcp | MCP server for external MCP clients | For `repoguard mcp` |
| fastapi, uvicorn, httpx | Web UI and API checks | For UI and API |
| playwright + Chromium, pillow, axe-playwright-python | Screenshots, visual diffs and accessibility | For visual checks |
| git | `repoguard fix` creates a branch, commits and pushes the new tests | For `repoguard fix` |
| `google-genai` (`pip install -e ".[vertex]"`) + Google Cloud credentials, or `ibm-watsonx-ai` (`pip install -e ".[ai]"`) + IBM Cloud credentials | Writing tests (`repoguard fix`) and the optional `--summarize` prose | For AI features only — measurement never needs it |

The mutation engine is built on Python's standard `ast` module. It doesn't depend on mutmut or Stryker.

## Tech stack

Status key: ✅ implemented and running in this repo · ⚠️ implemented but not verified end to end · 🗺️ planned (design doc only, no code yet)

| Area | Technology | Used for | Status |
|---|---|---|---|
| Language | Python ≥ 3.10 | Engine, CLI, API, MCP server | ✅ |
| Test execution | pytest, pytest-cov | Running the target repo's suite | ✅ |
| Coverage | coverage.py | Line coverage per file | ✅ |
| Mutation testing | Python stdlib `ast` (own engine, 6 operators) | Injecting bugs, mutation score (16/79 on demo-repo, deterministic) | ✅ |
| CLI | Click, Rich | `repoguard analyze · fix · gate · serve · mcp` | ✅ |
| Web API | FastAPI 0.141.1, Starlette 1.7.0 (pinned together), Uvicorn | `repoguard serve`: `/api/analyze`, `/api/summary`, `/api/fix` (Autofix, token-gated, streamed NDJSON) | ✅ |
| Live progress | Server-Sent Events (`StreamingResponse` → browser `EventSource`) | `/api/stream` step-by-step progress | ✅ |
| API checks | stdlib `ast` + httpx | Finding FastAPI routes, flagging untested ones, `GET` smoke tests | ✅ |
| Visual checks | Playwright (Chromium), Pillow | Screenshots and pixel diff (MCP tools) | ✅ locally · not in the Docker image (no Chromium) |
| Accessibility | axe-playwright-python (axe-core) | Accessibility violations (MCP tool) | ✅ locally · not in the Docker image |
| Agent protocol | MCP via FastMCP (stdio) | 9 tools for any MCP client | ✅ |
| AI (watsonx.ai provider) | IBM watsonx.ai (`ibm-watsonx-ai`), default model `mistralai/mistral-small-3-1-24b-instruct-2503` | Writer and critic agents with tool calling (`repoguard fix`), `--summarize` prose | ✅ live-verified with real credentials — `--summarize` returns real generated text; `repoguard fix`'s tool-calling round trip runs for real, though this default model doesn't reliably invoke tools (a model-choice quality gap, not an SDK/plumbing issue — see `PENDING.md` Phase 16) |
| Multi-agent swarm | Parallel agent lanes (`ThreadPoolExecutor`), per-lane sandboxes, file-based agent contract | Parallel Test Writer / Verifier / Critic per file, parallel mutation workers | 🟢 `fix --swarm` built, S0–S7 verified with no credentials (89.87%, 71/79); real-model benchmark pending ([design](docs/MULTI_AGENT_SWARM.md)) |
| AI provider abstraction | `ChatProvider` protocol (`repoguard_engine/ai_providers/`) | Switching between providers without touching the agents (`REPOGUARD_AI_PROVIDER` / `--provider`) | ✅ Phase 16 Stage A ([details](docs/MULTICLOUD_AI.md)) |
| AI (default provider) | Google Vertex AI (`google-genai`, Gemini, `gemini-3.8-flash`) | Default model provider (`ai_providers.DEFAULT_PROVIDER`) — no free-tier rate limits, unlike watsonx.ai's shared pool | ✅ live-verified: real text generation and a full tool-calling round trip against a real GCP project ([details](docs/VERTEX_SETUP.md)) |
| Frontend | Next.js 16.3.6, React 19.2.8, TypeScript 5, ESLint 9 | `web-next/` dashboard | ✅ (lint + build pass; end-to-end checked in a browser locally) |
| Legacy UI | Static HTML served by FastAPI | `repoguard serve` dashboard | ✅ |
| Charts (docs) | matplotlib (`[docs]` extra) | README before/after image | ✅ |
| Charts (dashboard) | Recharts | Trend, survival-by-operator and fix-effect charts | 🟡 backend routes done (`/operators`, `/survivors`, `/flaky`, plus `/trend`/`/risk-heatmap`); `web-next` charts themselves still 🗺️ Phase 17 C1 ([design](docs/DATA_PLATFORM.md#6-charts-web-next-dashboard)) |
| Container | Docker (`python:3.11-slim`) | Single image for Cloud Run | ✅ builds and deploys via `cd.yml` |
| CI | GitHub Actions: `ci.yml`, `frontend-ci.yml` | Verify checks, tests, coverage gate, mutation determinism, frontend lint/build | ✅ green on `main` |
| CD | GitHub Actions: `cd.yml` | Build → Artifact Registry → Cloud Run | ✅ deploys on every push to `main` via Workload Identity Federation ([`docs/DEPLOY.md`](docs/DEPLOY.md)) |
| Cloud (backend) | Google Cloud Run, Artifact Registry | Hosting the API + dashboard | ✅ deployed and live, called by the Vercel frontend below |
| Cloud (frontend) | Vercel | Hosting `web-next/` | ✅ deployed: https://ibm-bob-mcp-agent-guard.vercel.app/, calling the Cloud Run backend (`NEXT_PUBLIC_REPOGUARD_API_BASE`) |
| Database | PostgreSQL 16 (Cloud SQL, live) + SQLite locally | Run history per commit | ✅ store built and verified on SQLite + Postgres 16 (Phase 17 A1); live Cloud SQL instance provisioned and wired to the deployed service (Phase 17 B1, [design](docs/DATA_PLATFORM.md#4-database-design)) |
| Data access | SQLAlchemy 2 (Core), psycopg 3 (`[db]` extra) | One code path for SQLite and Postgres | ✅ `repoguard_engine/store/` |
| Infrastructure as code | Terraform (google, random providers), local state (gitignored) | Provisioning GCP | ✅ CI/CD identity (Artifact Registry, deployer SA, WIF) + Cloud SQL/Secret Manager (Phase 17 B1, [design](docs/DATA_PLATFORM.md#8-infrastructure-as-code-terraform)) |
| Secrets | Google Secret Manager | Database password + Autofix bearer token | ✅ `repoguard-database-url` and `repoguard-fix-token`, both live on the deployed service |
| CD authentication | Workload Identity Federation (GitHub OIDC) | Replacing the JSON service-account key | ✅ done since Phase 13, now Terraform-managed |
| User accounts | Google Identity Platform | Optional sign-in for the dashboard | 🗺️ Phase 17, below the cut line |
| Version control | git | `repoguard fix --publish`: branch, commit, push | ✅ |
| Diagrams | Mermaid | Architecture and ER diagrams in the docs | ✅ |
| Built with | IBM Bob IDE | Authored Phases 0–8 ([evidence](docs/IBM_BOB_USAGE.md)) | ✅ (retired afterwards) |
| Built with | Claude Code | Authored Phase 13 onward | ✅ |

## Project structure

```
ibm-bob-mcp-agent-guard/
├── .bob/                           Where IBM Bob built Phases 0–8 (docs/IBM_BOB_USAGE.md); config kept for history
├── .github/workflows/
│   ├── ci.yml                      Backend CI: verify.py checks, demo-repo tests, coverage gate, mutation determinism, scripted fix loop, store round trip
│   ├── frontend-ci.yml             web-next/ lint + build (path-filtered)
│   ├── infra-ci.yml                terraform fmt -check + validate (path-filtered, no credentials)
│   └── cd.yml                      Build image → Artifact Registry → deploy to Cloud Run on push to main
├── Dockerfile                      Single image: `repoguard serve` + bundled demo-repo/
│
├── infra/terraform/                CI/CD identity (Artifact Registry, deployer SA, WIF pool/provider) — codifies Phase 13, applied for real
├── scripts/
│   ├── verify.py                   Phase verification gate — every PENDING.md phase has a check here
│   └── verify_phase17.py           Store round-trip checks (imported by verify.py)
│
├── repoguard_engine/               Core library + all entry points
│   ├── __init__.py
│   ├── core.py                     Coverage measurement, gap detection, mutation testing, risk score, dashboard
│   ├── api_check.py                FastAPI endpoint discovery (AST) + HTTP smoke tests
│   ├── visual.py                   Playwright screenshots, pixel diff, console logs, axe-core a11y
│   ├── narrative.py                AI prose summary of an already-measured dashboard (never a metric source)
│   ├── ai_providers/               ChatProvider abstraction: base.py, watsonx.py, vertex.py
│   ├── watson_agent/               AI fix loop: guarded tools, prompts, orchestrator
│   ├── swarm/                      Multi-agent swarm (Phase 18): sandbox, guard, plan, lanes, critic, fan-in, Gate, report
│   ├── testing/                    Credential-free ScriptedProvider (Phase 18 Step 0) — drives the fix loop with no AI credentials
│   ├── store/                      Run history (optional [db] extra): run record, SQLAlchemy tables + views, writer
│   ├── pipeline.py                 Ordered pipeline: measure → gaps → risk → gate
│   ├── cli.py                      CLI entry point: analyze | fix | gate | serve | mcp
│   ├── mcp_server.py               9 MCP tools via FastMCP (stdio transport)
│   └── web/
│       ├── __init__.py
│       ├── server.py               FastAPI app — REST + SSE stream
│       └── static/index.html       Web dashboard UI
│
├── demo-repo/                      Fixture: intentionally under-tested e-commerce shop
│   ├── pytest.ini
│   ├── shop/
│   │   ├── __init__.py
│   │   ├── api.py                  FastAPI routes (7 endpoints)
│   │   ├── cart.py                 Cart logic
│   │   ├── inventory.py            Inventory management
│   │   └── pricing.py              Pricing and discount rules
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_api.py             Weak baseline API tests
│   │   ├── test_cart.py            Weak baseline cart tests
│   │   └── test_pricing.py         Weak baseline pricing tests
│   └── web/index.html              Simple shop UI (for visual checks)
│
├── docs/
│   ├── ARCHITECTURE.md             Layer diagram, data flow, MCP tool list
│   ├── ARCHITECTURE-front.md       The web-next/ Next.js dashboard on Vercel
│   ├── DEMO.md                     3-minute demo script
│   ├── DEPLOY.md                   One-time GCP setup for the Cloud Run deploy
│   ├── DATA_PLATFORM.md            Phase 17: run history on Postgres (store built, A1), Terraform (WIF built), data-driven charts
│   ├── MULTICLOUD_AI.md            ChatProvider abstraction — watsonx.ai + Vertex AI, both built and live-verified
│   ├── WATSONX_SETUP.md            IBM Cloud credentials for the watsonx.ai provider
│   ├── VERTEX_SETUP.md             GCP credentials for the Vertex AI provider
│   ├── MULTI_AGENT_SWARM.md        Phase 18 swarm design + build steps — S0–S7 built
│   ├── EVAL_GUARDRAILS_PLAN.md            Phase 19 plan: fix-loop guardrails, evaluation, benchmark
│   ├── EVAL_GUARDRAILS_IMPLEMENTATION.md  Phase 19 build steps and verify.py checks
│   ├── AI_ASSISTED_DEVELOPMENT_FRAMEWORK.md  How this project itself is built (Claude, file-based contract)
│   ├── make_results_chart.py       Generates the before/after results chart
│   ├── expected-after-tests/       Reference tests (copy here to verify "after" numbers)
│   └── img/                        README badge images
│
├── bob-evidence/                   Template for exporting IBM Bob session reports (never populated — see docs/IBM_BOB_USAGE.md
│                                    for the real evidence instead); repoguard fix now writes its own run report to
│                                    <target-repo>/watson-evidence/, same convention as repoguard-out/ (AGENTS.md §4)
│
├── AGENTS.md                       Agent context and coding rules (kept byte-identical to CLAUDE.md)
├── RUNBOOK.md                      Operational runbook (install, run, troubleshoot)
├── README.md                       This file
├── pyproject.toml                  Package metadata and dependencies
├── .gitignore
└── .bobignore
```

## CI/CD

Four GitHub Actions workflows, split so a frontend-only or infra-only change
never triggers the Python/mutation pipeline or a Cloud Run deploy:

| Workflow | Trigger | What it runs |
|---|---|---|
| [`ci.yml`](.github/workflows/ci.yml) | Push to `main`, every PR (ignores `web-next/**`) | 4 jobs: `quality-gate` (`verify.py phase0`/`phase7`, demo-repo pytest, `repoguard gate --threshold 60`), `mutation-determinism` (`phase3`, two full runs must match 16/79), `fix-loop-stub` (`phase18-seq-stub`, scripted fix loop), `store` (`phase17-store`/`phase17-pipeline` against real SQLite + Postgres 16) |
| [`frontend-ci.yml`](.github/workflows/frontend-ci.yml) | Changes under `web-next/**` | `npm run lint` + `npm run build` |
| [`infra-ci.yml`](.github/workflows/infra-ci.yml) | Changes under `infra/terraform/**` | `terraform fmt -check` + `terraform validate`, no GCP credentials needed |
| [`cd.yml`](.github/workflows/cd.yml) | Push to `main` (ignores `web-next/**`), or manual | Builds the `Dockerfile`, pushes to Artifact Registry, deploys to Cloud Run |

The coverage gate threshold (60.0%) sits just under the measured 60.3%
baseline, so it fails on a real regression instead of always or never.

## Deploy to Google Cloud

The backend (`repoguard serve`: API + dashboard + bundled `demo-repo/`)
deploys to **Cloud Run** through `cd.yml`. The one-time GCP setup (project,
Artifact Registry, service account, Workload Identity Federation) is done —
see [`docs/DEPLOY.md`](docs/DEPLOY.md) for exactly what was created. Auth
uses WIF, not a long-lived JSON key: GitHub Actions exchanges its own OIDC
token for short-lived Google credentials at run time, so no GCP secret is
ever stored in the repo. `cd.yml` deploys on every push to `main` once the
GitHub repo variables (`WIF_PROVIDER`, `DEPLOYER_SA`, etc. — see
`docs/DEPLOY.md` §2) are set.

Known limits of today's deploy: the service is public
(`--allow-unauthenticated`, fine for a judged demo), and the container's
filesystem is ephemeral, so results in `repoguard-out/` are lost when an
instance stops. The next section plans a fix for that.

The Next.js dashboard (`web-next/`) is a separate Vercel project — see
[`docs/ARCHITECTURE-front.md`](docs/ARCHITECTURE-front.md).

## Database

> `PENDING.md` Phase 17. **Built:** the store and pipeline hook (A1); per-mutant
> and per-test history loaded into the store, with `v_survival_by_operator`/
> `v_persistent_survivors`/`v_flaky_tests` views (A2-gap); read routes and CI
> ingest, including `/operators`/`/survivors`/`/flaky` (A3/C1 backend); a real
> Cloud SQL instance provisioned and wired to the deployed service (B1). **Not
> yet:** the `web-next` charts themselves (C1 frontend) and `/fix-effect`
> (needs a `fix_sessions` table, a separate task).

Every run used to write `repoguard-out/*.json` and forget. With
`REPOGUARD_DATABASE_URL` set, `repoguard analyze` / `gate` and the MCP
`tool_full_pipeline` also store the run (coverage, per-file missing lines,
mutation score, risk ranking, endpoints, git commit/branch/dirty state) in
**SQLite or PostgreSQL** through one SQLAlchemy code path:

```bash
pip install -e ".[db]"
export REPOGUARD_DATABASE_URL=sqlite:///repoguard-history.db   # or postgresql://user:pass@host/db
repoguard analyze ./demo-repo --mutation --project demo
# ... Stored run 3f2c…  (project demo)
```

Rules carried over from `AGENTS.md §4`:

- The engine measures; the database only stores. Values are stored exactly as measured (`Double`, no rounding: coverage is stored as `60.264900662251655`, not `60.3`); `passed_gate`, deltas and trends are SQL views, never stored numbers.
- Persistence is off unless `REPOGUARD_DATABASE_URL` is set, and cannot change a measured number (`verify.py phase17-pipeline` checks that the `repoguard-out/*.json` files are byte-identical with and without it). A bad URL or a missing `[db]` extra fails before measuring, not after.
- The public web API never writes: `/api/analyze` doesn't store runs, even with the variable set, until per-project tokens exist (A3).
- Every run stores the mutation operator set's hash; trends are drawn only between runs that used the same operators.

| Topic | Link |
|---|---|
| Why a database, and what "data-driven" QA uses history for | [§1](docs/DATA_PLATFORM.md#1-why-a-database-now) |
| Engine changes the schema depends on | [§4.1](docs/DATA_PLATFORM.md#41-engine-changes-the-schema-depends-on) |
| ER diagram (12 tables) | [§4.2](docs/DATA_PLATFORM.md#42-entity-relationship-diagram) |
| SQL views behind every chart | [§4.4](docs/DATA_PLATFORM.md#44-views-all-derived-values-live-here) |
| Risk model v2 — calibrated against stored data | [§5](docs/DATA_PLATFORM.md#5-risk-model-v2--calibrated-not-invented) |
| Dashboard charts | [§6](docs/DATA_PLATFORM.md#6-charts-web-next-dashboard) |
| API additions | [§7](docs/DATA_PLATFORM.md#7-api-additions-webserverpy-thin-over-store) |
| Build order and cut line | [§10](docs/DATA_PLATFORM.md#10-build-steps-two-day-hackathon-order) |
| Verification (`verify.py phase17`) | [§11](docs/DATA_PLATFORM.md#11-verification) |

## Infrastructure as code

> `PENDING.md` Phase 17, blocks B1–B2. **Built:** the CI/CD identity — Artifact
> Registry, the `repoguard-deployer` service account + roles, and the
> Workload Identity Federation pool/provider that lets `cd.yml` deploy
> without a JSON key — plus a real Cloud SQL for PostgreSQL 16 instance,
> database, user and a Secret Manager secret holding the connection string,
> wired onto the deployed Cloud Run service.

**Terraform** (`infra/terraform/`) codifies the WIF identity that
`docs/DEPLOY.md` §1 originally created by hand via `gcloud` for Phase 13 —
`terraform import` adopted the live resources, and `terraform plan` against
the real project confirms "No changes" (`infra/terraform/README.md`) — plus
`db.tf`, new infrastructure applied fresh (no import needed): Cloud SQL,
its database/user, and the `repoguard-database-url` secret, with IAM grants
scoping the Cloud Run runtime service account to just that secret and
`roles/cloudsql.client`. Cloud Run itself stays outside Terraform (still
deployed by `cd.yml`'s `gcloud run deploy`); wiring the database and the
`REPOGUARD_FIX_TOKEN` secret onto the live service was a documented human
step (`infra/terraform/README.md`), now done.
`infra-ci.yml` runs `terraform fmt -check` + `validate` on every change under
`infra/terraform/**`, with no credentials. Terraform owns identity only; CD
keeps deploying the image, and the frontend stays on Vercel, outside
Terraform's scope. `terraform apply` for anything new still needs a person
with GCP access and billing, same as `docs/DEPLOY.md`. Full layout and
decisions: [`docs/DATA_PLATFORM.md` §8](docs/DATA_PLATFORM.md#8-infrastructure-as-code-terraform).

## IBM Bob Usage

TestMind AI was built with **IBM Bob**, which authored the project's
foundation and all of Phases 0–8: the initial engine (`core.py`,
`api_check.py`, `visual.py`, `cli.py`, `pipeline.py`, `mcp_server.py`), the
`demo-repo/` fixture, and its own `.bob/` swarm configuration, then
completed the mutation engine (Phase 3), MCP compact responses (Phase 7)
and the Test Writer/Critic/Publisher subagent modes (Phase 8). Full
PR-by-PR and commit-by-commit evidence — including the exact "Made with IBM
Bob" / "PR description generated by IBM Bob" footers — is in
[`docs/IBM_BOB_USAGE.md`](docs/IBM_BOB_USAGE.md); the raw dashboard export
is in [`bob-evidence/README.md`](bob-evidence/README.md).

| Metric | Value |
|---|---|
| Bob commits | 12 | 
| PR | 4 | 

<table>
<tr>
<td><img src="bob-evidence/bob-images/b/10-bob-ide-2026-09-25_16-42-home-welcome-screen-recent-tasks.png" width="220" alt="IBM Bob IDE welcome screen"><br/><sub>IBM Bob IDE, this project's workspace</sub></td>
<td><img src="bob-evidence/bob-images/a/3-bob-ide-2026-09-25_15-05-github-pr-title-description-draft-markdown.png" width="220" alt="IBM Bob drafting a GitHub PR description"><br/><sub>Bob drafting a PR description</sub></td>
<td><img src="bob-evidence/bob-images/a/9-bob-ide-2026-09-25_15-45-phase0-complete-summary-verification-pass.png" width="220" alt="IBM Bob completing Phase 0 with a verify.py PASS"><br/><sub>Phase 0 closed, verify.py PASS</sub></td>
</tr>
<tr>
<td><img src="bob-evidence/bob-images/b/11-bob-ide-2026-09-25_16-35-phase8-test-writer-subagent-mode-setup.png" width="220" alt="IBM Bob setting up the Phase 8 Test Writer subagent mode"><br/><sub>Phase 8: Test Writer subagent mode</sub></td>
<td><img src="bob-evidence/bob-images/c/21-bob-ide-2026-09-25_17-49-project-testmind-ai-phase-status-table.png" width="220" alt="IBM Bob's phase-status table for this project"><br/><sub>Bob tracking this project's phase status</sub></td>
<td align="center"><a href="bob-evidence/bob-images/"><sub>26 screenshots total →<br/>bob-evidence/bob-images/</sub></a></td>
</tr>
</table>

### Phases 0–8

| Phase | What | Built by |
|---|---|---|
| 0 — Project skeleton | `pyproject.toml`, `AGENTS.md`, `scripts/verify.py` | IBM Bob |
| 1 — demo-repo fixture | `shop/*.py`, `tests/*`, `web/index.html` | IBM Bob |
| 2 — Core measurement | `core.py` (tests, coverage, gaps) | IBM Bob |
| 3 — Mutation engine | Own AST engine, replacing `mutmut` | IBM Bob |
| 4 — Risk score & dashboard | `compute_risk()` | IBM Bob |
| 5 — API check | `api_check.py` | IBM Bob |
| 6 — Visual testing | `visual.py` | IBM Bob |
| 7 — MCP server | `mcp_server.py`, compact responses | IBM Bob |
| 8 — Bob modes, rules, skills | `.bob/custom_modes.yaml`, guardrail hooks, subagent modes | IBM Bob |

### Bob's PRs

| PR | Title | Footer (exact) | Commits |
|---|---|---|---|
| #1 | feat(guardrails): safety hook, evidence export, verify-before-pr skill & AI dev framework | 🤖 *Created with IBM Bob* | 3 |
| #2 | feat(skeleton): Phase 0 — project skeleton verified | "Made with IBM Bob" (commit + PR body) | 1 |
| #4 | feat(engine): replace mutmut with own AST mutation engine; MCP compact responses | 🤖 *PR description generated by IBM Bob* | 2 |
| #6 | feat(modes): Phase 8 — Test Writer, Critic and Publisher subagent modes + test-writer skill | 🤖 *PR description generated by IBM Bob* | 3 |

Full commit-level breakdown (including 3 pre-PR-#1 direct pushes and the
initial commit) is in [`docs/IBM_BOB_USAGE.md`](docs/IBM_BOB_USAGE.md).

From Phase 13 onward (containerization, reference tests, the results chart,
and this session's watsonx.ai fix loop), Claude continued the build — see
[AI-Assisted Development](#ai-assisted-development) below for how that
handoff is documented and how the repo is built today.

## AI-Assisted Development

Two separate things in this project use AI, and it's worth being precise about which is which:

- **Building this repo**: IBM Bob authored Phases 0–8 (above); Claude has authored every engine/docs change from Phase 13 onward, working under the same explicit, file-based contract Bob used rather than ad-hoc prompting.
- **The product's own AI feature** is multicloud (Google Vertex AI by default, or IBM watsonx.ai), used at runtime for two things: `repoguard fix` (writes tests, guarded to `tests/` only) and `repoguard analyze --summarize` (plain-English prose from already-measured numbers, never a metric source). See [Using the AI fix loop](#using-the-ai-fix-loop) above.

The rest of this section is about the first one — how the repo itself gets built.

### The contract: context files in the repo

| File | Role |
|---|---|
| `AGENTS.md` (kept byte-identical to `CLAUDE.md`) | Architecture rules, layer boundaries, the token budget, and the actions that need human sign-off (Section 8). Loaded on every task. |
| `PENDING.md` | The prioritized roadmap, phase by phase. Read to pick the next task; items are checked off as they land. Never delete or empty it. |
| `LASTCONTEXT.md` | Current state, kept short: which phase is done, which is in progress, decisions in force, what's waiting on the user, known gotchas (e.g. "mutation score flakes without `PYTHONDONTWRITEBYTECODE`"). A new session reads this instead of re-deriving context. |
| `docs/ARCHITECTURE.md` | Operational knowledge — the data contract in `repoguard-out/`, the MCP tool list, the watsonx.ai fix loop. |

### What happens end to end
- **Verify before claiming done:** every phase in `PENDING.md` has a matching check in `scripts/verify.py`. The relevant check's output is pasted into the PR before marking a phase complete — a claim without a PASS doesn't count.
- **Git workflow:** one short-lived branch per phase (`feat/03-mutation`, `feat/15-watsonx-migration`, …), Conventional Commits, a PR description with the verify output as the test plan. Every commit carries a `Co-Authored-By` trailer.
- **Documentation:** keeps README, `AGENTS.md`/`CLAUDE.md`, `PENDING.md` and the measured numbers in `docs/` in sync with each change — a number in the docs must always match what `verify.py` just measured.
- **Diagnosis:** when a check fails (e.g. the mutation score isn't deterministic), the job is to find the real cause before patching around it — see `AGENTS.md` Section 9, "Known pitfalls," for the ones already found (bytecode caching, animation timing, ambient-PATH subprocess calls, missing watsonx.ai credentials).

## Documentation

- [IBM Bob Usage](docs/IBM_BOB_USAGE.md): full PR- and commit-level evidence for Phases 0–8
- [Hackathon submission status](docs/HACKATHON_SUBMISSION_STATUS.md): checklist tracking against the lablab.ai submission requirements
- [Architecture](docs/ARCHITECTURE.md): diagrams, the sequence of a run, MCP tools and the data contract
- [Demo script](docs/DEMO.md): 3-minute pitch and backup plan
- [Deploy to Cloud Run](docs/DEPLOY.md): one-time GCP setup for the CD workflow
- [Data platform (design)](docs/DATA_PLATFORM.md): run history on Postgres, Terraform on GCP, data-driven charts
- [Multi-agent swarm](docs/MULTI_AGENT_SWARM.md): parallel Test Writer / Verifier / Critic lanes per file, fan-in and a single Gate — IBM Bob's swarm design, rebuilt provider-agnostic
- [Evaluation & guardrails (plan)](docs/EVAL_GUARDRAILS_PLAN.md): benchmark landscape, measured gaps in today's fix loop, the three layers (guardrails, evaluation, observability), decisions
- [Evaluation & guardrails (implementation)](docs/EVAL_GUARDRAILS_IMPLEMENTATION.md): step-by-step build of Phase 19, with signatures and `verify.py phase19` checks
- [Frontend architecture](docs/ARCHITECTURE-front.md): the Next.js dashboard on Vercel
- [watsonx.ai setup](docs/WATSONX_SETUP.md): IBM Cloud credentials for the watsonx.ai provider
- [Multicloud AI](docs/MULTICLOUD_AI.md): the `ChatProvider` abstraction, watsonx.ai + Vertex AI (both built), and model benchmarking (planned)
- [Vertex AI setup](docs/VERTEX_SETUP.md): GCP credentials for the second AI provider
- [AI-Assisted Development Framework](docs/AI_ASSISTED_DEVELOPMENT_FRAMEWORK.md): how this repo itself is built — contract files and git workflow

## Roadmap

**Next.js dashboard on Vercel: built, deployed, live against Cloud Run.**
`web-next/` is on `main` and deployed at
https://ibm-bob-mcp-agent-guard.vercel.app/ — `RepoForm`/`ActionBar` drive
`/api/analyze`, `StreamLog` renders `/api/stream` live,
`StatCards`/`GapsList`/`RiskTable` render the measured numbers verbatim, and
`SummaryPanel` shows the advisory AI summary from `POST /api/summary`,
labeled with the provider that wrote it. The public URL calls the real
backend on Cloud Run; checked end to end in a real browser (Analyze on
`./demo-repo`: 60.3% coverage, 4 gap files, gate FAIL). The current web UI (`repoguard serve`,
`web/static/index.html`) stays as the reference implementation — the new
frontend consumes the same endpoints rather than replacing them.

**Site restructure: nav, footer, and four new screens.** `web-next/` is now a
small multi-page site, not a single dashboard: a shared `SiteNav`/`SiteFooter`
(`web-next/app/components/site/`) links **Analyze** (`/`, the dashboard
above), **Results** (`/results`, a run-history view — reads `fetchProjects`/
`fetchView` and shows "Run history isn't on this backend yet" until it's
wired to Phase 17 A3/C1's read routes, which now exist and return real data
on the deployed service — the frontend wiring itself is a separate,
not-yet-done task), **Project** (`/project`), **Technical**
(`/technical`) and **AI-assisted dev** (`/ai-development`) — the last three
are explainer pages covering the same ground as this README's sections, laid
out for someone who lands on the deployed site instead of GitHub.

The AI summary works on the public demo (`provider: vertex`). **Autofix** is
built: with a token, the button runs the AI fix loop through `POST /api/fix`
on a temporary copy of the repo. Progress streams live, and the result shows
the engine-measured before → after plus the test files written. Nothing is
committed. `REPOGUARD_FIX_TOKEN` is now attached on Cloud Run
(`docs/DEPLOY.md` §5) — the endpoint correctly returns `401` for a missing/
wrong token instead of the earlier `503` disabled state; a full first live
run from the public demo (measured before/after) is still pending. The frontend gets no Terraform or
GCP infrastructure: it ships as a plain Vercel project, with its own
path-filtered CI (`.github/workflows/frontend-ci.yml`). See `PENDING.md`
Phase 14 and `docs/ARCHITECTURE-front.md`.

**Run history for the backend.** The store, per-mutant/per-test history,
read routes, and a live Cloud SQL instance wired to the deployed service are
all built (Phase 17 A1–A3, B1). What's left is the `web-next` dashboard
charts themselves (C1) and `/fix-effect` (needs a `fix_sessions` table). See
[Database](#database) and [Infrastructure as code](#infrastructure-as-code)
above (`PENDING.md` Phase 17).

**Multi-agent swarm: built, benchmark pending.** `repoguard fix --swarm`
(S0–S7) is verified with no credentials: 89.87% (71/79). Still to do: real
Vertex/watsonx runs against the sequential loop (speed and final score),
the lanes view in the web UI, and a CI job. See [Multi-agent swarm](#multi-agent-swarm)
(`PENDING.md` Phase 18).

**Evaluation and guardrails: built.** G1–G6, O1 and the held-out fixture
(E3) run in CI. The repeated fix-loop benchmark (E2) is built and needs
real-model credentials to run. See [Evaluation & guardrails](#evaluation--guardrails)
(`PENDING.md` Phase 19).

**Multicloud AI: built; model benchmarking still planned.** See
[`docs/MULTICLOUD_AI.md`](docs/MULTICLOUD_AI.md) (`PENDING.md` Phase 16) —
`repoguard_engine/ai_providers/` holds a `ChatProvider` abstraction with
watsonx.ai and Google Vertex AI behind it (`REPOGUARD_AI_PROVIDER` /
`--provider` select the backend), both live-verified. Still planned: a
benchmark script to compare models by measured mutation-score deltas rather
than opinion, which needs live credentials for both clouds at once.

## Limitations

- Python + pytest only. API checks support FastAPI only.
- Equivalent mutants (changes with no observable effect) are reported, not filtered out automatically.
- The accessibility check is basic. Use axe-core for a full audit.
- `repoguard fix` needs real credentials for the selected provider (`docs/WATSONX_SETUP.md` or `docs/VERTEX_SETUP.md`); without them it fails with a clear error rather than degrading silently. Live-verified this session with real watsonx.ai credentials: `--summarize` generates real text, and the fix loop's tool-calling round trip runs for real — though watsonx.ai's default model doesn't reliably invoke tools (see `PENDING.md` Phase 16), which is why Vertex AI (Gemini) was added and is now the default provider.

## Author

**Agustin Diaz-Cano** M.Sc. Candidate, Information Systems Engineering - [UTN](https://frba.utn.edu.ar/)

[LinkedIn](https://www.linkedin.com/in/agustindiazcano/) · [Portfolio](http://www.agustindiazcano.com/) · [ORCID](https://orcid.org/0009-0001-4336-490X) · [Google Scholar](https://scholar.google.com/citations?user=qUcRD6UAAAAJ&hl=en)

## Team

Team Argentina
