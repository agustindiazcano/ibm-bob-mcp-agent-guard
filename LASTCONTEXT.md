# Last Context

> **Purpose:** Snapshot of the current working session — what was done, what decisions were made, and where things stand. Read this at the start of every new session before touching any file.

---

## Project

**TestMind AI** (`ibm-bob-mcp-agent-guard`) — AI-powered QA agent swarm built on IBM Bob + MCP.  
CLI / package name: `repoguard`. GitHub: https://github.com/agustindiazcano/ibm-bob-mcp-agent-guard

---

## Session summary

### What was done in this session

| # | Action | Files affected |
|---|---|---|
| 1 | Initialized git repo, connected to GitHub remote, pushed initial commit | all project files |
| 2 | Created `RUNBOOK.md` — full operational runbook (install, CLI, dashboard, MCP, Bob swarm, CI gate, troubleshooting) | `RUNBOOK.md` |
| 3 | Expanded `## Project structure` in `README.md` with full annotated file tree | `README.md` |
| 4 | Expanded `## 5. Directory layout` in `AGENTS.md` with full annotated file tree | `AGENTS.md` |
| 5 | Replaced `## 11. Git` in `AGENTS.md` with `## 11. Git and workflow` — added branch-per-phase rule, `verify.py` gate, and doc-sync rule | `AGENTS.md` |
| 6 | Added session-start instruction at the top of `AGENTS.md` | `AGENTS.md` |
| 7 | Created `LASTCONTEXT.md` (this file) and `PENDING.md` | `LASTCONTEXT.md`, `PENDING.md` |

### Key decisions made

- `RUNBOOK.md` is the operational reference; `AGENTS.md` is the agent/coding reference — they are complementary, not duplicated.
- Project tree in both `README.md` and `AGENTS.md` reflects the actual repo state including `RUNBOOK.md` and `LASTCONTEXT.md`/`PENDING.md`.
- `AGENTS.md` section 11 now enforces a `scripts/verify.py` gate before PRs — script does not exist yet (see PENDING).

---

## Current repo state

- Branch: `main`
- Last commit: `docs: add RUNBOOK.md and expand project tree in README and AGENTS`
- All changes pushed to origin

---

## How to resume

1. Read `PENDING.md` for the task list.
2. Check `git log --oneline -5` to confirm the commit you're on.
3. Run `repoguard analyze ./demo-repo` to verify the engine baseline before any code change.
