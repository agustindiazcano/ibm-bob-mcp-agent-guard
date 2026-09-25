# RepoGuard — Runbook

Operational reference for installing, running, and troubleshooting RepoGuard in development and CI environments.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [CLI Reference](#3-cli-reference)
4. [Running the Web Dashboard](#4-running-the-web-dashboard)
5. [Running the MCP Server](#5-running-the-mcp-server)
6. [Bob Integration (Swarm)](#6-bob-integration-swarm)
7. [CI Gate Setup](#7-ci-gate-setup)
8. [Demo Fixture](#8-demo-fixture)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

| Requirement | Minimum version | Notes |
|---|---|---|
| Python | 3.11 | Required by `pyproject.toml` |
| pip | 23+ | For `pip install -e .` |
| IBM Bob IDE | current | Required for `fix` mode and MCP integration |
| Node.js | 18+ | Only needed if Bob's MCP transport is stdio |
| Playwright | latest | Only needed for visual / a11y checks |
| mutmut | latest | Only needed for `--mutation` flag |

---

## 2. Installation

### Standard install (editable)

```bash
git clone https://github.com/agustindiazcano/ibm-bob-mcp-agent-guard.git
cd ibm-bob-mcp-agent-guard
pip install -e .
```

This registers the `repoguard` CLI entry point defined in [`pyproject.toml`](pyproject.toml).

### Verify the install

```bash
repoguard --help
```

Expected output lists five sub-commands: `analyze`, `fix`, `gate`, `serve`, `mcp`.

### Optional: Playwright browsers (visual checks only)

```bash
pip install playwright
playwright install chromium
```

---

## 3. CLI Reference

All commands accept a `REPO_PATH` argument (default: `.`).

### `repoguard analyze`

Measure test coverage and quality gaps in a target repository.

```bash
# Basic coverage analysis
repoguard analyze ./my-project

# Include mutation testing (slow — adds mutmut run)
repoguard analyze ./my-project --mutation

# Detect untested FastAPI endpoints
repoguard analyze ./my-project --endpoints

# Output raw JSON (useful for scripting / piping)
repoguard analyze ./my-project --json-output
```

Output: a **Coverage Summary** table and a **Top Risk Files** table printed to stdout.

### `repoguard gate`

CI-oriented command. Exits with code `1` if coverage is below the threshold.

```bash
# Default threshold: 80 %
repoguard gate ./my-project

# Custom threshold
repoguard gate ./my-project --threshold 90
```

Exit codes:
- `0` — coverage ≥ threshold (gate passed)
- `1` — coverage < threshold (gate failed)

### `repoguard fix`

Instructs the user to use Bob's MCP integration. This command does not run autonomously from the terminal; it is designed to be invoked by Bob as an MCP tool.

```bash
repoguard fix ./my-project   # Prints instructions; use Bob instead
```

### `repoguard serve`

Start the real-time web dashboard.

```bash
repoguard serve                         # Default: http://127.0.0.1:8000
repoguard serve --host 0.0.0.0 --port 9000
```

### `repoguard mcp`

Start the MCP server over stdio transport so Bob can connect.

```bash
repoguard mcp
```

---

## 4. Running the Web Dashboard

1. Start the server:
   ```bash
   repoguard serve
   ```
2. Open `http://127.0.0.1:8000` in a browser.
3. The dashboard auto-refreshes via SSE (`GET /api/stream`).

### REST endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Serves `index.html` |
| `GET` | `/api/analyze` | Runs the full pipeline synchronously, returns JSON |
| `GET` | `/api/stream` | SSE stream of pipeline progress events |

---

## 5. Running the MCP Server

The MCP server exposes **8 tools** over stdio transport. Start it with:

```bash
repoguard mcp
```

### Available MCP tools

| Tool | Description |
|---|---|
| `tool_measure_coverage` | Run pytest with coverage; return percent, line counts |
| `tool_find_gaps` | Coverage measurement + structured gap report |
| `tool_run_mutation` | Run mutation testing via mutmut; return score |
| `tool_find_untested_endpoints` | Detect FastAPI routes with no corresponding test |
| `tool_smoke_test_endpoints` | Fire minimal HTTP requests at each detected endpoint |
| `tool_full_pipeline` | Full pipeline: coverage → gaps → risk → gate |
| `tool_capture_screenshot` | Playwright screenshot of a URL |
| `tool_check_accessibility` | axe-core a11y checks on a URL |

### Connecting Bob to the MCP server

Add an entry to Bob's MCP configuration (`.bob/mcp.json`) pointing to the stdio process:

```json
{
  "mcpServers": {
    "repoguard": {
      "command": "repoguard",
      "args": ["mcp"]
    }
  }
}
```

---

## 6. Bob Integration (Swarm)

RepoGuard ships six custom Bob modes defined in [`.bob/custom_modes.yaml`](.bob/custom_modes.yaml).

### Agent roles

| Mode slug | Name | Responsibility |
|---|---|---|
| `orchestrator` | RepoGuard Orchestrator | Coordinates the full swarm; never writes code |
| `analyzer` | RepoGuard Analyzer | Measures coverage, gaps, and mutation score |
| `fixer` | RepoGuard Fixer | Writes tests to close the gaps reported by Analyzer |
| `gate` | RepoGuard Gate | Validates thresholds after fixes; pass/fail verdict |
| `visual-agent` | RepoGuard Visual Agent | Screenshots, pixel diffs, console logs, a11y |
| `reporter` | RepoGuard Reporter | Produces the final report in `bob-evidence/` |

### Recommended swarm workflow

```
Orchestrator
  │
  ├─ 1. Analyzer  →  measure_coverage / find_gaps / find_untested_endpoints
  ├─ 2. Fixer     →  write tests under tests/
  ├─ 3. Gate      →  re-run full_pipeline, check threshold
  ├─ 4. Visual Agent  →  screenshot / a11y (optional, web UI repos only)
  └─ 5. Reporter  →  write summary to bob-evidence/
```

### Key rules enforced on the Fixer sub-agent

- **Rule 01** — only create or modify files inside `tests/`
- **Rule 02** — always run measurement before proposing any fix
- **Rule 03** — tests must be mutation-resistant with specific assertions

---

## 7. CI Gate Setup

### GitHub Actions example

```yaml
name: Quality Gate

on: [push, pull_request]

jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e .
      - run: repoguard gate . --threshold 80
```

The job fails (exit code `1`) if coverage drops below the threshold, blocking the merge.

---

## 8. Demo Fixture

The [`demo-repo/`](demo-repo/) directory contains an intentionally under-tested e-commerce application used to demonstrate RepoGuard's full workflow.

```bash
# Analyse the demo repo
repoguard analyze ./demo-repo

# Run the gate against the demo repo (expected to fail initially)
repoguard gate ./demo-repo --threshold 80
```

See [`docs/DEMO.md`](docs/DEMO.md) for a full walkthrough.

---

## 9. Troubleshooting

### `repoguard: command not found`

The package is not installed in the active environment. Run:

```bash
pip install -e .
which repoguard   # confirm the entry point exists
```

### `No coverage data`

pytest found no tests or the `tests/` directory is missing. Ensure:
- There is at least one `test_*.py` file under `tests/`.
- `pytest` can be run standalone in the target repo without errors.

### `repoguard gate` exits 1 unexpectedly

Check the actual coverage percentage in the table output and compare against your `--threshold`. Use `repoguard analyze` for a detailed gap report to identify which files need more tests.

### MCP server not connecting to Bob

1. Confirm `repoguard mcp` starts without error when run manually.
2. Check that the MCP entry in `.bob/mcp.json` uses the correct command and path.
3. Restart Bob after updating `mcp.json`.

### Visual tools fail (`capture_screenshot`, `check_accessibility`)

Playwright browsers must be installed separately:

```bash
pip install playwright
playwright install chromium
```

### Mutation testing is very slow

Run `--mutation` only on targeted files, not the whole repo:

```bash
repoguard analyze ./my-project --mutation
```

Or invoke the MCP tool directly with a scoped path:

```json
{ "tool": "tool_run_mutation", "repo_path": "./my-project", "paths_to_mutate": "shop/pricing.py" }
```
