# RepoGuard — Agent Context

RepoGuard is a Python CLI + MCP server that measures test quality in any repo and drives Bob to fix the gaps.

## Project Layout

```
repoguard/
├── repoguard_engine/       # Core library
│   ├── core.py             # Tests, coverage, gaps, mutation, risk, dashboard
│   ├── api_check.py        # Untested FastAPI endpoints + smoke tests
│   ├── visual.py           # Screenshots, pixel diff, console logs, a11y
│   ├── pipeline.py         # Pipeline execution (measure / bob mode)
│   ├── cli.py              # CLI: repoguard analyze | fix | gate | serve | mcp
│   ├── mcp_server.py       # 8 MCP tools via FastMCP
│   └── web/                # FastAPI + SSE dashboard
├── demo-repo/              # Demo fixture: e-commerce with intentionally weak tests
├── docs/                   # Architecture, demo, build guide
└── bob-evidence/           # Evidence collected during Bob-driven runs
```

## Tech Stack

- **Python** ≥ 3.11
- **FastAPI** — web dashboard and REST API
- **FastMCP** — MCP server exposing 8 tools
- **pytest + coverage.py** — test measurement
- **SSE (Server-Sent Events)** — real-time dashboard updates
- **CLI entry point** — `repoguard` (configured in `pyproject.toml`)

## CLI Commands

```
repoguard analyze   # Measure test coverage and quality gaps
repoguard fix       # Bob-driven fix loop
repoguard gate      # CI gate: fail if quality thresholds not met
repoguard serve     # Start web dashboard
repoguard mcp       # Start MCP server
```

## Key Conventions

- All measurement before action: measure → report → fix → re-measure
- Tests live in `tests/` alongside source packages
- MCP tools are thin wrappers over `repoguard_engine` functions
- The web dashboard consumes the same data as the CLI

## Bob Modes (`.bob/custom_modes.yaml`)

- **Orchestrator** — coordinates the swarm
- **5 sub-agents** — specialized roles (analyze, fix, gate, visual, report)

## Rules

1. `01-tests-only.md` — only write/modify test files unless explicitly told otherwise
2. `02-measure-dont-guess.md` — always run measurement tools before proposing fixes
3. `03-test-quality.md` — quality standards for generated tests
