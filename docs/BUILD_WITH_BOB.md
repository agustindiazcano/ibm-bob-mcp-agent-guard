# Building RepoGuard with Bob

This document captures how RepoGuard was built using Bob as an AI pair programmer.

## Setup

1. Install Bob IDE or Bob Shell.
2. Open this repository.
3. Bob reads `AGENTS.md` automatically — no manual context loading needed.

## Bob Modes Used

| Mode | Purpose |
|---|---|
| Agent (default) | Writing engine code, CLI, MCP server |
| Plan | Designing the pipeline architecture and data model |
| Orchestrator | End-to-end fix cycles on the demo-repo |

## Key Bob Commands Used During Development

```
/init                        # Generate AGENTS.md from codebase
repoguard analyze .          # Measure RepoGuard's own test coverage
repoguard gate . --threshold 80
```

## Skills Activated During Development

- `pytest-conventions` — activated when writing any test file
- `mutation-hunting` — activated when improving test quality for the engine

## Rules Enforced

All three rules in `.bob/rules/` were active throughout:

- Bob never modified `repoguard_engine/` source files when asked to "fix tests"
- Bob always ran `tool_measure_coverage` before proposing changes
- Generated tests consistently met the quality standards in rule 03

## Evidence

See `bob-evidence/` for screenshots, before/after coverage reports, and conversation logs.
