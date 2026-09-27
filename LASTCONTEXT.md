# Last Context

> **Purpose:** Snapshot of the current working session — what was done, what decisions were made, and where things stand. Read this at the start of every new session before touching any file.

---

## Project

**TestMind AI** (`ibm-bob-mcp-agent-guard`) — AI-powered QA agent swarm built on IBM Bob + MCP.  
CLI / package name: `repoguard`. GitHub: https://github.com/agustindiazcano/ibm-bob-mcp-agent-guard

---

## Session summary

### Session 27 — Phase 19 G1-G6 + O1, on `feat/19-guardrails-g1-g5`

| # | Action | Files affected |
|---|---|---|
| 1 | Implemented G1 (`pytest_env` allow-list), G2 (`policy.py` static test checks, D1 approved), G3 (`acceptance.py` per-file gate: repetition/canary/preservation/whole-suite), G4 (harness-`error` outcome class), G5 (`FixResult.status`/`integrity`, evidence always written), G6 (source-only coverage, D9 approved, `ci.yml` threshold → 60.0) | `repoguard_engine/core.py`, `mutation.py`, `watson_agent/{acceptance,policy,orchestrator,tools}.py`, `.github/workflows/ci.yml` |
| 2 | Fixed a regression in `ScriptedProvider.chat()` (rewritten to expect a turn format `scripts/phase19_scripts.py` never produces — `KeyError: 'name'` on 7/8 attack scripts, with the 8th "passing" only because it hit the same exception) | `repoguard_engine/ai_providers/scripted.py` |
| 3 | Implemented O1 (`repoguard-out/fix_run.json`) and fixed two crash bugs found validating it: `_write_fix_run` called in `run_fix_loop`'s `finally` but never defined (`NameError` on every run); `_timing_section` joined `tool_calls` as strings after this same change made them dicts (`TypeError`) | `repoguard_engine/watson_agent/orchestrator.py` |
| 4 | Committed 1-3 as `5a49404` | — |
| 5 | Found the `verify.py phase19` 1800s timeout is too short for a real Windows box (measured baseline 290s + after-with-71-tests 362s + G3 subprocess overhead) — raised to 3600s | `scripts/verify_phase19.py` |
| 6 | Live-verified Vertex AI works from this checkout (`--summarize`, real coverage 60.3%, coherent AI prose referencing the real numbers) | — |
| 7 | Found and fixed a real environment bug: the `repoguard` console script's editable install pointed at a sibling worktree (`-phase17-18`), silently measuring *that* branch's code under a bare `repoguard` invocation — repointed with `pip install -e ".[ai,vertex,db,docs]"` from this checkout; documented in `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` §9 | `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` |
| 8 | Found `CLAUDE.md` had drifted from `AGENTS.md`/`GEMINI.md` (still had the pre-G6 65.1% coverage numbers) — synced | `CLAUDE.md` |
| 9 | Found (not yet resolved) a direct `run_mutation` timing measurement with the 4 reference tests scored 88.61% (70/79), not the documented 89.87% (71/79) that E1's `honest` check asserts exactly — judged non-blocking/likely flakiness per user decision (core `AGENTS.md §7` baseline re-measured unaffected: 20.25%, 16/79) | `PENDING.md` |

Verification status: `verify.py phase19` rerunning with the 3600s timeout at session end (not yet confirmed PASS — see PENDING.md's "Known issue"). 11 (merge) and 12 (Vertex benchmark, E2) approved by user this session; not yet executed.

---

### Session 26 — Phase 19 E1: Scripted Provider (`feat/19-eval-scripted-provider`)

| # | Action | Files affected |
|---|---|---|
| 1 | Implemented `ScriptedProvider` for Phase 19 step E1 to inject 8 scripted attack vectors and an honest run | `repoguard_engine/ai_providers/scripted.py` |
| 2 | Added Phase 19 test scripts (P1-P8 attack vectors) and `phase19` verification | `scripts/phase19_scripts.py`, `scripts/verify_phase19.py`, `scripts/verify.py` |
| 3 | Updated `PENDING.md` Phase 19 E1 to done (🟢) | `PENDING.md` |

Verified: `verify.py phase19` passed (using stubs for mutation speed, pending G1-G5).

---

## How to resume

1. Read `PENDING.md` for the task list (Phase 11 is now 🟢 — read its "3 attempts, 3 bugs" narrative before touching `watson_agent/` again, it explains real, non-obvious API constraints).
2. Run `python scripts/verify.py phase0`, `phase3`, `phase7`, `phase15`, `phase16`, `multicloud`, `phase14fix`, `phase14ui` (needs `npm ci` in `web-next/`), `phase18-seq-stub` (and, with `[db]`, `phase17-store`, `phase17-pipeline`, `phase17-endpoints`, `phase17-api`, `phase18-s1`, `phase17-engine`) to confirm baseline holds. All four of `phase18-s1`/`phase17-engine`/`phase17-endpoints`/`phase17-api` are wired into `ci.yml` on `ci/wire-phase17-phase18-checks` (Session 25, one consolidated branch) but it isn't merged yet — merge it (or re-verify and redo the wiring) before assuming CI actually covers them.
3. Frontend punch-list items 1-4 are all done and verified live (Session 21). Autofix (`POST /api/fix`, Phase 14 gap 3) is built (Session 22); what's left is the human token step (Session 25 confirmed `gcloud secrets create` is genuinely blocked for an agent session) plus a first live run. When pushing follow-up commits to a branch mid-session, confirm with `git log origin/main..<branch>` that nothing merged out from under you first (Session 21 item 5, and again in Session 24 — a cherry-pick's conflicts were resolved but `--continue` was never run; always check `git log`/`git status` after resolving conflicts, don't trust that the files look right).
4. Phase 17/18 next steps: **S3** (per-lane sandbox + write guard, next up for the swarm) and the **A2-gap** (load per-mutant/per-test records into the SQL store — unblocks `operators`/`fix-effect`/`survivors`/`flaky`, the 4 A3 routes Session 25 deliberately didn't build because the data isn't there yet). Both still build from `docs/DATA_PLATFORM.md` §13 / `docs/MULTI_AGENT_SWARM.md` §14, not their original sketches. Decision #1 (JUnit test id) is still open. `web-next/app/results/` (`history.ts`) isn't wired to any of Session 25's new routes yet — a real, separate frontend task, not automatic just because the backend exists now.
5. Autofix: attach `REPOGUARD_FIX_TOKEN` (`docs/DEPLOY.md` §5), then run it from the Vercel demo against `demo-repo` and record the measured before/after. If you change a Vercel env var, Redeploy the **newest `main`** deployment, never an older row (`docs/ARCHITECTURE-front.md`, Session 21-front item 5).
6. If tightening `repoguard-deployer`'s IAM roles, or moving the new `aiplatform.user` grant into Terraform: read `infra/terraform/README.md`'s "Known gap" section first — real permissions change against a live project, own PR.
7. The repo-rename decision is open and low-urgency — decide whenever, it's cosmetic.
8. Phase 19 G1-G6 + O1 are done (Session 27, commit `5a49404` on `feat/19-guardrails-g1-g5`) — check `verify.py phase19`'s result first (was rerunning with a 3600s timeout at session end; read its output before trusting either the timeout fix or the 88.61%/89.87% discrepancy noted in `PENDING.md`'s "Known issue"). If it PASSes (or the known issue is still judged non-blocking), open the PR, then move to step 9 (E2 `scripts/eval_fixloop.py`, credentialed — approved) and step 11 (merge — approved); Vertex AI credentials are confirmed working from this checkout (`VERTEX_PROJECT_ID=project-e0ad10c9-0b2f-4dc0-ac6` in `.env`, ADC already present). Before running anything through the bare `repoguard` command, `pip show repoguard`'s "Editable project location" must say this checkout, not a sibling worktree (Session 27 pitfall, `AGENTS.md §9`).
9. `claude/eager-gauss-ifyd8w` is superseded (Session 24) — delete it whenever convenient, nothing in it is unmerged real work. If a new session gets assigned that branch name again by the harness, don't assume its history is relevant; diff it against `main` first.