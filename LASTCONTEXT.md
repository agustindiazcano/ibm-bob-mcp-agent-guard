# Last Context

> **Purpose:** Snapshot of the current working session — what was done, what decisions were made, and where things stand. Read this at the start of every new session before touching any file.

---

## Project

**TestMind AI** (`ibm-bob-mcp-agent-guard`) — AI-powered QA agent swarm built on IBM Bob + MCP.  
CLI / package name: `repoguard`. GitHub: https://github.com/agustindiazcano/ibm-bob-mcp-agent-guard

---

## Session summary


### Session 27 — Phase 18 S4: lane state machine, thread pool, blackboard (`feat/18-s4-lane-blackboard`)

| # | Action | Files affected |
|---|---|---|
| 1 | Built `swarm/blackboard.py`: the `repoguard-out/swarm/<run_id>/` file contract — schema-tagged JSON, atomic tmp+`os.replace` writes, `.test.py.txt`-only snapshot guard (never `.py` — it would become a mutation target), `Timeline` behind one lock. 15 new unit tests, no lane/runner involved | `repoguard_engine/swarm/blackboard.py`, `repoguard_engine/swarm/tests/test_blackboard.py` |
| 2 | Built the lane runner: `plan.py` (`build_plan`, posix-normalized join keys — coverage.py's `missing_lines` keys are OS-native, mutation's are posix), `verify.py` (the Verifier: suite-first, then file-scoped mutation joined by fingerprint, plus a coverage-based `newly_covered` check), `lane.py` (the state machine + best-round-wins ranking + catch-all `FAILED`), `runner.py` (all sandboxes created serially up front via `ExitStack`, one shared mutation pool, lanes in their own thread pool) | `repoguard_engine/swarm/{plan,verify,lane,runner}.py` |
| 3 | Added `verify.py phase18-s4`: real 4-lane run against a temp demo-repo copy with `ScriptedProvider`, `workers=4` vs `workers=1`, plus a permanently-failing writer and a raising writer script | `scripts/verify_phase18.py`, `scripts/verify.py` |
| 4 | Updated `PENDING.md` Phase 18 S4 to done (🟢); synced `AGENTS.md`/`CLAUDE.md`'s `swarm/` directory listing | `PENDING.md`, `AGENTS.md`, `CLAUDE.md` |

Verified: `verify.py phase18-s4` PASS — 4/4 lanes `ACCEPTED` round 1 with real
kills, `regressed == []`, `timeline.jsonl` shows 4 overlapping lane spans,
every recorded sandbox gone after the run, real `tests/` untouched,
`workers=1`/`workers=4` give identical `verify-1.json` records, a
permanently-failing writer ends `FAILED` after 2 rounds, a raising writer
script is caught and reported `FAILED` without crashing the run, demo-repo
byte-identical throughout. No critic (S5), no fan-in/Gate (S6), no
`--swarm` CLI/web entry point yet — a lane's result never reaches the real
`tests/` dir.

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
4. Phase 18 next step: **S5** (read-only critic, JSON verdict, one revision round) then **S6** (fan-in, Gate, Publisher, Reporter, `--swarm` CLI flag) — S0-S4 are all done (Session 27 finished S4: `swarm/{blackboard,plan,verify,lane,runner}.py`, `verify.py phase18-s4` PASS). Build from `docs/MULTI_AGENT_SWARM.md` §14 Step 5/6, not the original sketch. A lane's accepted test currently never reaches the real `tests/` dir — that's what S6's fan-in adds. Decision #1 (JUnit test id) is still open. `web-next/app/results/` (`history.ts`) isn't wired to any of Session 25's new routes yet — a real, separate frontend task, not automatic just because the backend exists now.
5. Autofix: attach `REPOGUARD_FIX_TOKEN` (`docs/DEPLOY.md` §5), then run it from the Vercel demo against `demo-repo` and record the measured before/after. If you change a Vercel env var, Redeploy the **newest `main`** deployment, never an older row (`docs/ARCHITECTURE-front.md`, Session 21-front item 5).
6. If tightening `repoguard-deployer`'s IAM roles, or moving the new `aiplatform.user` grant into Terraform: read `infra/terraform/README.md`'s "Known gap" section first — real permissions change against a live project, own PR.
7. The repo-rename decision is open and low-urgency — decide whenever, it's cosmetic.
8. Phase 19: build from `docs/EVAL_GUARDRAILS_IMPLEMENTATION.md` in step order. Steps 1, 3, 4, 5, 7 and 8 need no approval; step 2 needs D1, step 6 needs D9. Step 4 (sham mutant + outcome classes) overlaps what Phase 18 S1/S2 already built (Session 24) — check `mutation.py`'s `MutationEnvironmentError` before rebuilding it.
9. `claude/eager-gauss-ifyd8w` is superseded (Session 24) — delete it whenever convenient, nothing in it is unmerged real work. If a new session gets assigned that branch name again by the harness, don't assume its history is relevant; diff it against `main` first.