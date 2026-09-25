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
└────────────┬──────────────────────────┬─────────────┘
             │                          │
┌────────────▼────────┐   ┌─────────────▼─────────────┐
│   MCP Server        │   │   Web Dashboard (FastAPI)  │
│   mcp_server.py     │   │   web/server.py + SSE      │
│   (8 FastMCP tools) │   │   web/static/index.html    │
└─────────────────────┘   └───────────────────────────┘
```

## Component Responsibilities

### `repoguard_engine/core.py`
- `measure_coverage(repo_path)` — runs `pytest --cov --cov-report=json`, parses `coverage.json`
- `find_coverage_gaps(coverage)` — derives uncovered files and lines from a CoverageResult
- `run_mutation(repo_path, ...)` — runs `mutmut`, parses killed/survived counts
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
- FastMCP server exposing 8 tools (thin wrappers over engine functions)
- Started via `repoguard mcp` (stdio transport)

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

## Bob Integration (Swarm)

Bob connects to the MCP server (`repoguard mcp`) and uses the 8 tools to:
1. Measure → `tool_measure_coverage` / `tool_find_gaps`
2. Prioritise → `tool_run_mutation` / `tool_find_untested_endpoints`
3. Fix → Bob writes tests directly (Fixer sub-agent)
4. Validate → `tool_full_pipeline` with gate threshold
5. Report → `tool_capture_screenshot` / `tool_check_accessibility` for visual evidence

The Orchestrator mode in `.bob/custom_modes.yaml` coordinates this flow across sub-agents.
