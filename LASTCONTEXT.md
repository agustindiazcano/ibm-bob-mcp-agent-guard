# Last Context

> **Purpose:** Snapshot of the current working session — what was done, what decisions were made, and where things stand. Read this at the start of every new session before touching any file.

---

## Project

**TestMind AI** (`ibm-bob-mcp-agent-guard`) — AI-powered QA agent swarm built on IBM Bob + MCP.  
CLI / package name: `repoguard`. GitHub: https://github.com/agustindiazcano/ibm-bob-mcp-agent-guard

---

## Session summary

### Session 1 (previous)

| # | Action | Files affected |
|---|---|---|
| 1 | Initialized git repo, connected to GitHub remote, pushed initial commit | all project files |
| 2 | Created `RUNBOOK.md` | `RUNBOOK.md` |
| 3 | Expanded project tree in `README.md` and `AGENTS.md` | `README.md`, `AGENTS.md` |
| 4 | Added branch-per-phase / verify.py gate rules to `AGENTS.md §11` | `AGENTS.md` |
| 5 | Created `LASTCONTEXT.md` and `PENDING.md` | both |

### Session 2 — Phase 0 completion

| # | Action | Files affected |
|---|---|---|
| 1 | Fixed `pyproject.toml`: corrected build-backend (`setuptools.build_meta`), set `requires-python = ">=3.10"`, added `playwright` and `pillow` deps | `pyproject.toml` |
| 2 | Added `repoguard-out/` and `**/repoguard-out/` exclusions | `.gitignore`, `.bobignore` |
| 3 | Created `scripts/verify.py` with `phase0` check | `scripts/verify.py` |
| 4 | Installed package with `pip install -e . --no-deps`; confirmed `repoguard --help` shows all 5 subcommands | — |
| 5 | `python scripts/verify.py phase0` → **PASS** | — |
| 6 | Marked all Phase 0 deliverables 🟢 in `PENDING.md` | `PENDING.md` |

### Key decisions made

- `build-backend` was wrong (`setuptools.backends.legacy:build` → `setuptools.build_meta`); fixed.
- `playwright` and `pillow` added as required by AGENTS.md §3 tech stack.
- `scripts/verify.py` is a thin gate script; extend it per phase as work progresses.

---

### Session 3 — Phase 3 (mutation engine) + Phase 7 (MCP compact responses)

| # | Action | Files affected |
|---|---|---|
| 1 | Replaced `mutmut`-based `run_mutation()` with own AST engine using `ast.NodeTransformer`; 6 operator classes (comparison, arithmetic, boolean, constants, return None, remove raise); temp-copy isolation with `PYTHONDONTWRITEBYTECODE=1`; tempdir cleanup after each mutant | `repoguard_engine/core.py` |
| 2 | Added `repoguard-out/` write logic to `measure_coverage()`, `find_coverage_gaps()`, `run_mutation()`, `compute_risk()` — closes the "contract between agents" gap | `repoguard_engine/core.py` |
| 3 | Added `timeout=` to all `subprocess.run()` calls in `core.py` | `repoguard_engine/core.py` |
| 4 | Added `detail: bool = False` param to all 8 MCP tools; compact/full response split | `repoguard_engine/mcp_server.py` |
| 5 | Updated `AGENTS.md §7` verification table with measured numbers (5 tests, 65.1% coverage, 20.25% mutation 16/79) | `AGENTS.md` |
| 6 | Added `phase3` and `phase7` checks to `scripts/verify.py`; added `timeout=` to all subprocess calls in that file | `scripts/verify.py` |
| 7 | Marked Phase 3 "Determinism" and Phase 7 "Compact responses" 🟢 in `PENDING.md` | `PENDING.md` |
| 8 | Created `phase3-7-plan.md` (plan file for this work) | `phase3-7-plan.md` |

### Key decisions (Session 3)

- **Mutation score**: new AST engine produces 20.25%, 16/79 (not the old mutmut 23.6%, 17/72 — different engine, different mutant count, as expected).
- **demo-repo test count**: only 5 tests pass (not 9 as documented); `AGENTS.md §7` corrected to 5.
- **Coverage**: 65.1% (not 74.5%); corrected in `AGENTS.md §7`.
- **`repoguard fix`** (Phase 9) deferred to its own branch — depends on Phases 4–6 and Bob Shell invocation is unverified.
- **`compute_risk()` formula** is still a stub (coverage gap only, not complexity×churn×detection); deferred to Phase 4.
- `find_coverage_gaps()` signature changed to accept optional `repo_path` for writing `gaps.json` — callers passing only `coverage` still work (default is `None`).

### Session 4 — Sync README with the new AST engine's measured numbers

`feat/03-mutation` was merged to `main` and independently re-verified (clean venv,
`verify.py phase0/phase3/phase7` all PASS, `run_mutation` reproduced 20.25%/16/79
twice, `git status` clean afterward — no leakage from the temp-copy isolation).
`AGENTS.md §7` was already correct from that PR; `README.md` was not — it still
showed the old `mutmut`-era before/after table. Per `AGENTS.md §11` ("a number in
the docs must always match what `verify.py` just measured"), that's a same-PR
requirement, not optional polish.

| # | Action | Files affected |
|---|---|---|
| 1 | Replaced README's before-numbers (9 tests / 74.5% / 23.6% (17/72)) with the measured AST-engine numbers (5 tests / 65.1% / 20.25% (16/79)) | `README.md` |
| 2 | Marked the after-column `TBD` instead of carrying over the old `mutmut`-era after-numbers (66 tests / 100% / 94.4%), since the reference tests haven't been re-run against the new engine yet | `README.md` |
| 3 | Noted in-page that the interim `mutmut`-based figures are superseded, so a reader doesn't assume the old badge/table was ever wrong on its own terms | `README.md` |

### Key decisions (Session 4)

- Never carry forward an unmeasured "after" number just to fill a table cell — `TBD` is honest, a guessed 94.4% would not be.
- `docs/img/results-en-{dark,light}.png` still don't exist (pre-existing gap, out of scope here); the alt text was updated to match reality regardless, since alt text is read even when the image itself is broken.

---

### Session 5 — Housekeeping + Phase 8 subagent modes

| # | Action | Files affected |
|---|---|---|
| 1 | Pulled main (PR #4 feat/03-mutation + PR #5 README sync already merged; local was stale) | — |
| 2 | Added `coverage.json` to `.gitignore` (untracked file nag) | `.gitignore` |
| 3 | Created `.gitattributes` (normalize line endings; resolves CRLF warnings on every commit) | `.gitattributes` |
| 4 | Deleted `phase3-7-plan.md` (working artifact, plan complete, no longer needed) | `phase3-7-plan.md` |
| 5 | Created branch `feat/08-bob-modes` | — |
| 6 | Added Test Writer mode (`test-writer`) to `custom_modes.yaml` | `.bob/custom_modes.yaml` |
| 7 | Added Critic mode (`critic`) to `custom_modes.yaml` | `.bob/custom_modes.yaml` |
| 8 | Added Publisher mode (`publisher`) to `custom_modes.yaml` | `.bob/custom_modes.yaml` |
| 9 | Updated Orchestrator `roleDefinition` with explicit 5-step pipeline and blocker conditions | `.bob/custom_modes.yaml` |
| 10 | Created `test-writer` skill with 7-step mutant-killing guide | `.bob/skills/test-writer/SKILL.md` |
| 11 | Updated `AGENTS.md` directory tree with new skills | `AGENTS.md` |
| 12 | Marked Phase 8 Test Writer, Critic, Publisher 🟢 and `.gitattributes` task done in `PENDING.md` | `PENDING.md` |

### Key decisions (Session 5)

- `LASTCONTEXT.md` did not reflect that PRs #4 and #5 were already merged — a drift that caused a stale "open PR" proposal. Fixed by pulling main before any other action. `LASTCONTEXT.md` must be updated at session end, not as an afterthought.
- `phase3-7-plan.md` deleted (plan served its purpose); moving to `docs/` would just defer the decision.
- Publisher mode given `execute` group (needs `git` + `gh` CLI calls) but no `edit` group (must not touch test files).
- Critic mode given `edit` group restricted to `tests/` by convention (enforced by Rule 01, not fileRegex, to keep the YAML readable).

### Session 6 — Role change: Bob out of code-authoring credits; Docker/CI-CD phase added

Bob has credits left to *run* the application (measurement, live demo) but not
to author new code. Until that changes, Claude writes the code directly —
`.bob/custom_modes.yaml`'s pipeline stays as the intended design (what Bob
runs once credits allow / what the live demo shows executing), it's just not
how code gets written meanwhile.

Two concrete gaps surfaced and got queued as a result:
1. `docs/expected-after-tests/*.py` — described in that folder's own README as
   the demo's Plan B, but the 4 files were never actually written. This blocks
   the README "After" column and is now explicitly a Claude task.
2. No containerization or CI/CD existed at all — added as a new **Phase 13**
   in `PENDING.md`, scoped to what Claude can actually do from here (write and
   locally verify a `Dockerfile` + two GitHub Actions workflows) versus what
   needs a human with real GCP access (creating the project, Artifact
   Registry, service account/WIF, repo secrets — Claude holds no cloud
   credentials and can't create cloud resources).

| # | Action | Files affected |
|---|---|---|
| 1 | Added a session note to `AGENTS.md §2` documenting the role change so a future session (Bob's or Claude's) doesn't assume the swarm is authoring code | `AGENTS.md` |
| 2 | Added Phase 13 (Containerization & CI/CD) to `PENDING.md`, with the human-vs-Claude split spelled out | `PENDING.md` |
| 3 | Added the missing reference-tests gap as an explicit standalone task | `PENDING.md` |

### Key decisions (Session 6)

- Don't rewrite `.bob/custom_modes.yaml` or the rules/skills — the swarm design is still correct, it's just temporarily not the thing writing code. Reverting or diluting that design would be the wrong fix for a credits problem.
- Docker/CI-CD is scoped honestly: Claude can produce and locally test the artifacts, but actual cloud deployment (creating GCP resources, holding credentials) is a human step — said explicitly in `PENDING.md` rather than implied.

---

## Current repo state

- Branch: `docs/claude-authors-code-and-cicd-plan` (on top of `main` at `fd6655c`)
- Phase 0: 🟢 · Phase 3: 🟢 · Phase 7: 🟢 · Phase 8: 🟢 (all complete)
- Phase 13 (Containerization & CI/CD): 🔴 just added, not started
- Remaining 🔴 critical-path items: `repoguard fix` (Phase 9), Phase 11 full run
- Bob: execution/demo only until credits for code authoring are restored

---

## How to resume

1. Read `PENDING.md` for the task list.
2. Run `python scripts/verify.py phase0`, `phase3`, `phase7` to confirm baseline holds.
3. Phase 13 (Docker + CI/CD) is next up for Claude — Dockerfile first, then CI workflow, then CD workflow, then hand the GCP setup steps to a human.
4. Separately: write `docs/expected-after-tests/*.py` (4 files) to unblock the README's "After" column without needing a live Bob run.
5. Still waiting on Bob credits: `repoguard fix` (Phase 9), Phase 11 first full end-to-end demo run.
