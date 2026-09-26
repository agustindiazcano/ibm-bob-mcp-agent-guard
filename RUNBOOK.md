# RepoGuard — Runbook

Operational reference for installing, running, and troubleshooting RepoGuard in development and CI environments.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [CLI Reference](#3-cli-reference)
4. [Running the Web Dashboard](#4-running-the-web-dashboard)
5. [Running the MCP Server](#5-running-the-mcp-server)
6. [watsonx.ai Fix Loop](#6-watsonxai-fix-loop)
7. [CI Gate Setup](#7-ci-gate-setup)
8. [Demo Fixture](#8-demo-fixture)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

| Requirement | Minimum version | Notes |
|---|---|---|
| Python | 3.11 | Required by `pyproject.toml` |
| pip | 23+ | For `pip install -e .` |
| `ibm-watsonx-ai` + IBM Cloud credentials | current | Required for `repoguard fix` and `analyze --summarize` only (`pip install -e ".[ai]"`, see `docs/WATSONX_SETUP.md`) |
| Playwright | latest | Only needed for visual / a11y checks |
| SQLAlchemy 2 + psycopg 3 | current | Only for run history (`pip install -e ".[db]"`, `REPOGUARD_DATABASE_URL`) — see below |

The mutation engine is built on Python's own `ast` module — no `mutmut` dependency.

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

### Optional: run history database (`[db]` extra)

```bash
pip install -e ".[db]"
export REPOGUARD_DATABASE_URL=sqlite:///repoguard-history.db    # or postgresql://user:pass@host:5432/db
repoguard analyze ./demo-repo --project demo                    # prints "Stored run <id> (project demo)"
```

- Unset → nothing is stored and SQLAlchemy is never imported.
- `postgres://` / `postgresql://` URLs use the psycopg 3 driver automatically.
- Project slug: `--project` > `REPOGUARD_PROJECT` > `GITHUB_REPOSITORY` > the repo directory name. In CI, pass `--project` when measuring a subdirectory, or the run is filed under the workflow's repository.
- A bad URL, an unreachable database or a missing `[db]` extra fails with `✗ Storage failed: …` (exit 1) **before** measuring.
- `repoguard serve`'s `/api/analyze` never stores runs, even with the variable set (public route; web writes wait for per-project tokens).
- Verify: `python scripts/verify.py phase17-store` (set `REPOGUARD_TEST_DATABASE_URL` to also check Postgres) and `phase17-pipeline`.

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

Runs the watsonx.ai fix loop: measures, has watsonx.ai write tests (guarded to `tests/` only), critiques them, measures again. Requires `WATSONX_APIKEY`/`WATSONX_PROJECT_ID` — see [section 6](#6-watsonxai-fix-loop).

```bash
repoguard fix ./my-project
repoguard fix ./my-project --publish            # also branch, commit and open a PR if the gate passes
repoguard fix ./my-project --threshold 90       # gate threshold for the after-measurement
```

### `repoguard serve`

Start the real-time web dashboard.

```bash
repoguard serve                         # Default: http://127.0.0.1:8000
repoguard serve --host 0.0.0.0 --port 9000
```

### `repoguard mcp`

Start the MCP server over stdio transport for any MCP client.

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

The MCP server exposes **9 tools** over stdio transport. Start it with:

```bash
repoguard mcp
```

### Available MCP tools

| Tool | Description |
|---|---|
| `tool_measure_coverage` | Run pytest with coverage; return percent, line counts |
| `tool_find_gaps` | Coverage measurement + structured gap report |
| `tool_run_mutation` | Run mutation testing with the own AST engine; return score |
| `tool_find_untested_endpoints` | Detect FastAPI routes with no corresponding test |
| `tool_smoke_test_endpoints` | Fire minimal HTTP requests at each detected endpoint |
| `tool_full_pipeline` | Full pipeline: coverage → gaps → risk → gate |
| `tool_capture_screenshot` | Playwright screenshot of a URL |
| `tool_check_accessibility` | axe-core a11y checks on a URL |
| `tool_generate_summary` | watsonx.ai prose summary of already-measured numbers (advisory only) |

### Connecting an MCP client

Point any MCP client's server config at the stdio process, e.g.:

```json
{
  "mcpServers": {
    "repoguard": {
      "command": "repoguard",
      "args": ["mcp"],
      "timeout": 600000
    }
  }
}
```

The `timeout` matters: a full mutation run on `demo-repo`'s 79 mutants takes
several minutes, and the default client timeout is usually much shorter
(`AGENTS.md §9`).

---

## 6. watsonx.ai Fix Loop

`repoguard fix` runs `repoguard_engine/watson_agent/`'s orchestrator — the
functional replacement for what used to be IBM Bob's custom modes (see
`.bob/DEPRECATED.md`). It's a single process, not parallel subagents:

```
Baseline measure (coverage, mutation, risk)
  │
  ├─ Prioritize up to 3 files by risk score
  ├─ Per file: watsonx.ai writes a test  →  write_test_file (tests/ only, guarded)
  ├─ Per file: watsonx.ai critiques it   →  same guard applies to any rewrite
  ├─ Re-measure for real (deterministic, no AI)
  └─ --publish + gate passes  →  branch, commit tests/, push, gh pr create
```

Requires `WATSONX_APIKEY` and `WATSONX_PROJECT_ID` (`pip install -e ".[ai]"`,
see `docs/WATSONX_SETUP.md`). Without them, `get_chat_model()` raises before
any measurement runs, so the failure is immediate, not after several minutes
of mutation testing.

### The write guard

`watson_agent/tools.py`'s `write_test_file` is the only tool watsonx.ai is
given that can write anything, and it rejects any path that doesn't resolve
under `<repo_path>/tests/` — a property of the tool itself, not a rule the
model is merely asked to follow.

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

### MCP server not connecting

1. Confirm `repoguard mcp` starts without error when run manually.
2. Check that the client's MCP server entry uses the correct command and an absolute path if `repoguard` isn't on that client's PATH.
3. Restart the client after updating its MCP config.

### `repoguard fix` fails immediately with a credentials error

Expected with no `WATSONX_APIKEY`/`WATSONX_PROJECT_ID` set — see `docs/WATSONX_SETUP.md`. This is a fail-loud check that runs before the baseline measurement, not a bug.

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
