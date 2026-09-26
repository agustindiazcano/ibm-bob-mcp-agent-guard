# RepoGuard Architecture

## Overview

RepoGuard is structured as four independent layers that communicate via well-defined interfaces:

```
┌─────────────────────────────────────────────────────┐
│                    CLI  (click)                      │
│  repoguard analyze | fix | gate | serve | mcp        │
└──────────────────────┬──────────────────────────────┘
                       │ imports
┌──────────────────────▼──────────────────────────────┐
│              repoguard_engine                        │
│  core.py · api_check.py · visual.py · pipeline.py   │
│  narrative.py · ai_providers/ · watson_agent/         │
└────────────┬──────────────────────────┬─────────────┘
             │                          │
┌────────────▼────────┐   ┌─────────────▼─────────────┐
│   MCP Server        │   │   Web Dashboard (FastAPI)  │
│   mcp_server.py     │   │   web/server.py + SSE      │
│   (9 FastMCP tools) │   │   web/static/index.html    │
└─────────────────────┘   └───────────────────────────┘
```

## Component Responsibilities

### `repoguard_engine/core.py`
- `measure_coverage(repo_path)` — runs `pytest --cov --cov-report=json`, parses `coverage.json`
- `find_coverage_gaps(coverage)` — derives uncovered files and lines from a CoverageResult
- `run_mutation(repo_path, ...)` — runs the own AST mutation engine, parses killed/survived counts
- `compute_risk(repo_path, coverage)` — scores each file by coverage gap ratio
- `build_dashboard_data(...)` — assembles a JSON-serialisable dict for the UI

### `repoguard_engine/api_check.py`
- `find_untested_endpoints(repo_path)` — walks the repo with `ast`, finds FastAPI route decorators, cross-references test files
- `run_endpoint_smoke_tests(base_url, endpoints)` — fires minimal HTTP requests via `httpx`

### `repoguard_engine/visual.py`
- `capture_screenshot(url, output_path)` — Playwright screenshot
- `pixel_diff(baseline, current)` — Pillow + NumPy pixel comparison
- `collect_console_logs(url)` — Playwright console event capture
- `check_accessibility(url)` — axe-core via axe-playwright-python

### `repoguard_engine/pipeline.py`
- `run_pipeline(repo_path, ...)` — orchestrates all measurement steps in order; returns `PipelineResult`

### `repoguard_engine/cli.py`
- Click group with five commands: `analyze`, `fix`, `gate`, `serve`, `mcp`
- Entry point registered in `pyproject.toml` as `repoguard`

### `repoguard_engine/mcp_server.py`
- FastMCP server exposing 9 tools (thin wrappers over engine functions)
- Started via `repoguard mcp` (stdio transport), usable by any MCP client

### `repoguard_engine/ai_providers/`
- `base.py` — `ChatProvider` protocol (`chat(messages, tools=, max_tokens=, timeout_ms=) -> dict`), `AIProviderError`
- `watsonx.py` — the default provider; `get_provider()` builds a watsonx.ai chat (tool-calling) connection, raises `WatsonxCredentialsError` immediately if `WATSONX_APIKEY`/`WATSONX_PROJECT_ID` aren't set
- `vertex.py` — Google Vertex AI; **Phase 16 Stage B, not built yet** (needs real GCP credentials to live-verify the SDK call shape)
- `__init__.py` — `get_provider(provider=None, model_id=None)` reads `REPOGUARD_AI_PROVIDER` (default `"watsonx"`), lazily imports the selected module

### `repoguard_engine/watson_agent/`
- `tools.py` — `TOOL_SCHEMAS`/`TOOL_REGISTRY`; `write_test_file` is the only write tool and hard-rejects any path outside `tests/`
- `prompts.py` — system prompts for the writer/critic stages
- `orchestrator.py` — `run_fix_loop(repo_path, ..., provider=None)`: measure → prioritize by risk → write → critique → re-measure → evidence report; calls `ai_providers.get_provider()`, provider-agnostic

### `repoguard_engine/web/server.py`
- FastAPI application with:
  - `GET /` — serves `index.html`
  - `GET /api/analyze` — synchronous pipeline run, returns JSON
  - `GET /api/stream` — SSE stream of pipeline progress events

## Data Flow (analyze command)

```
repoguard analyze ./demo-repo
  │
  ├─ run_pipeline(repo_path)
  │     ├─ measure_coverage()  →  CoverageResult
  │     ├─ find_coverage_gaps()  →  GapReport
  │     ├─ compute_risk()  →  list[RiskScore]
  │     └─ build_dashboard_data()  →  dict
  │
  └─ _print_coverage_table()  →  rich table to stdout
```

## AI fix loop Integration

`repoguard fix` runs `watson_agent.orchestrator.run_fix_loop()` in-process
against `pipeline`/`core`/`api_check` directly — the same layering as
`web/server.py`, not an MCP round-trip. It drives whichever provider
`ai_providers.get_provider()` returns (watsonx.ai by default, or Vertex AI
via `REPOGUARD_AI_PROVIDER=vertex`/`--provider vertex` once Stage B lands):
1. Measure → `run_pipeline(..., include_mutation=True, include_endpoints=True)`
2. Prioritise → up to 3 files by `compute_risk()`'s existing risk score
3. Fix → the AI provider writes a test per file through `write_test_file`, guarded to `tests/`
4. Critique → a second call to the same provider reviews the new test against the quality prompt
5. Validate → re-run `run_pipeline()` for real numbers; `--publish` opens a PR if the gate passes

This replaces what `.bob/custom_modes.yaml`'s Orchestrator/Test
Writer/Critic/Gate/Publisher modes did (see `.bob/DEPRECATED.md`) — IBM Bob
is retired. The MCP server (`mcp_server.py`) is unrelated to this loop; it's
a separate, generic integration for any MCP client, not specific to Bob or
to the fix loop.

## Planned: Next.js dashboard on Vercel

**Not built yet — roadmap only, see `PENDING.md` Phase 14.**

The current web UI (`web/static/index.html`, served by `web/server.py`) stays as the
reference implementation. The plan is a richer frontend, built separately and consuming
the same FastAPI endpoints (`/api/analyze`, `/api/stream`) rather than replacing them:

```
┌───────────────────────────────┐        ┌──────────────────────────────┐
│  Next.js dashboard (Vercel)   │  HTTP  │  repoguard_engine/web/server  │
│  charts, risk table, action   │ ─────▶ │  (FastAPI, unchanged)         │
│  buttons ("Autofix", "Gate")  │  + SSE │  /api/analyze · /api/stream   │
└───────────────────────────────┘        └──────────────────────────────┘
```

No Terraform, no GCP-specific IaC for this piece — Vercel builds and hosts the
Next.js app directly from the repo. This doesn't change the existing Cloud Run
CD pipeline (`docs/DEPLOY.md`, Phase 13); the Next.js app is an additional
frontend, not a replacement backend deploy target.
