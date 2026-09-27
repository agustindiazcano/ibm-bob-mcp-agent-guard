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

### Session 28 — Phase 17 A2-gap/C1 backend/B1 Cloud SQL, live Dockerfile bug fix

| # | Action | Files affected |
|---|---|---|
| 1 | Loaded per-mutant/per-test records into the store (Phase 17 A2-gap): new `mutants`/`test_results` tables, `SCHEMA_VERSION` 2, three new views (`v_survival_by_operator`, `v_persistent_survivors`, `v_flaky_tests`) | `repoguard_engine/store/{models,record,repository,views}.py`, `scripts/verify_phase17.py` (new `phase17-mutants-tests` check), `scripts/verify.py` — PR #69, then #70 fixed `phase17-pipeline`'s 900s timeout (too tight — a single mutation pass measured ~600s under load) |
| 2 | Backend read routes for Phase 17 C1: `/operators`, `/survivors`, `/flaky` | `repoguard_engine/store/queries.py`, `repoguard_engine/web/server.py`, new `phase17-history-routes` check — PR #71 |
| 3 | Rewrote `docs/DEMO.md` — the old script predated the Vercel/Cloud Run deploy entirely and had placeholder numbers | `docs/DEMO.md` — PR #72 |
| 4 | Phase 17 B1: Terraform `db.tf` — Cloud SQL Postgres 16, database, user, `repoguard-database-url` Secret Manager secret, IAM grants for the Cloud Run runtime SA | `infra/terraform/{db,variables,versions,outputs}.tf`, `infra/terraform/README.md` — PR #73, then **applied for real** against the live GCP project (user confirmed a trial billing account, cost not a concern) |
| 5 | Wired Cloud SQL + `REPOGUARD_FIX_TOKEN` onto the live Cloud Run service by hand (`gcloud run services update --add-cloudsql-instances --update-secrets`) | Live GCP state, not a file — see `infra/terraform/README.md`'s human-step section. Generating/writing the `REPOGUARD_FIX_TOKEN` secret's *value* was refused by the harness's own safety layer ("secret-store writes") even with authenticated `gcloud`; the user ran `gcloud secrets create` themselves, then the agent granted IAM access and wired it in (not blocked) |
| 6 | **Found and fixed a real live bug**: every `GET /api/projects*` route crashed with a raw `500` (no CORS header) on the deployed service, regardless of DB config — `store/queries.py` imports `sqlalchemy` at module level, before `_history_engine()`'s graceful check ever runs, and the Docker image never had the `[db]` extra (`Dockerfile` only had `[vertex]`) | `Dockerfile` — PR #74, confirmed fixed live (`/api/projects` 500 → 200 after `cd.yml` redeployed) |
| 7 | Updated `AGENTS.md`/`CLAUDE.md`/`PENDING.md`/`README.md`/this file for everything above | (this commit) |

Verified live end to end: `https://ibm-bob-mcp-agent-guard.vercel.app/` →
real Cloud Run backend → Analyze (65.1%/20.25%=16/79, matches `AGENTS.md
§7`) → Vertex AI summary → `/api/projects` and friends now `200` with real
data → `POST /api/fix` returns `401` (not `503`) confirming the Autofix
token is live, though a full measured Autofix run from the public demo is
still pending. Two Cloud SQL cold-start/CORS false alarms during testing
turned out to be transient (Cloud Run scale-to-zero); the real bug (#6)
only surfaced once Cloud SQL was actually wired up and logs were checked.

Also merged in this session, done by other parallel agents on separate
branches: Phase 18 S4 (lane state machine + thread pool, PR #75, two agents
split as lane-runner/blackboard and integrated by one of them) and Phase 19
G1-G5 guardrails (`feat/19-guardrails-g1-g5`, still finishing local
verification as of this writing — not yet merged, check `PENDING.md` Phase
19 before assuming it landed).

Parallel-agent lesson: **the two front-facing agents working on this repo at
once caused a real self-inflicted slowdown** — running multiple
mutation-heavy `verify.py` checks concurrently (this session's own
`phase17-pipeline`/`phase17-store`/`phase0`, plus the guardrails agent's
`phase19` in the other checkout) starved each other for CPU on the same
Windows machine, timing out a check that passed cleanly once re-run alone.
Not a code bug — a resource-contention artifact of running heavy local
verification from two sessions simultaneously. Prefer a git worktree (not
the shared main checkout) for any parallel work, and avoid launching more
than one mutation-heavy `verify.py` check across all active sessions at once
if avoidable.

---

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
3. Frontend punch-list items 1-4 are all done and verified live (Session 21). Autofix (`POST /api/fix`, Phase 14 gap 3) is built (Session 22); `REPOGUARD_FIX_TOKEN` is now attached on Cloud Run (Session 28 — `gcloud secrets create` genuinely needs a human, per Session 25's finding, but IAM grants and wiring the secret onto the service don't). What's left is a first full live run with a measured before/after from the public demo. When pushing follow-up commits to a branch mid-session, confirm with `git log origin/main..<branch>` that nothing merged out from under you first (Session 21 item 5, and again in Session 24 — a cherry-pick's conflicts were resolved but `--continue` was never run; always check `git log`/`git status` after resolving conflicts, don't trust that the files look right).
4. Phase 18 next step: **S5** (read-only critic, JSON verdict, one revision round) then **S6** (fan-in, Gate, Publisher, Reporter, `--swarm` CLI flag) — S0-S4 are all done (Session 27 finished S4: `swarm/{blackboard,plan,verify,lane,runner}.py`, `verify.py phase18-s4` PASS). Build from `docs/MULTI_AGENT_SWARM.md` §14 Step 5/6, not the original sketch. A lane's accepted test currently never reaches the real `tests/` dir — that's what S6's fan-in adds. Decision #1 (JUnit test id) is still open. `web-next/app/results/` (`history.ts`) isn't wired to any of Session 25's new routes yet — a real, separate frontend task, not automatic just because the backend exists now.
5. Autofix: `REPOGUARD_FIX_TOKEN` is attached (Session 28) — next is running it from the Vercel demo against `demo-repo` and recording the measured before/after. If you change a Vercel env var, Redeploy the **newest `main`** deployment, never an older row (`docs/ARCHITECTURE-front.md`, Session 21-front item 5).
6. If tightening `repoguard-deployer`'s IAM roles, or moving the new `aiplatform.user` grant into Terraform: read `infra/terraform/README.md`'s "Known gap" section first — real permissions change against a live project, own PR.
7. The repo-rename decision is open and low-urgency — decide whenever, it's cosmetic.
8. Phase 19 G1-G6 + O1 are done (Session 27, commit `5a49404` on `feat/19-guardrails-g1-g5`) — check `verify.py phase19`'s result first (was rerunning with a 3600s timeout at session end; read its output before trusting either the timeout fix or the 88.61%/89.87% discrepancy noted in `PENDING.md`'s "Known issue"). If it PASSes (or the known issue is still judged non-blocking), open the PR, then move to step 9 (E2 `scripts/eval_fixloop.py`, credentialed — approved) and step 11 (merge — approved); Vertex AI credentials are confirmed working from this checkout (`VERTEX_PROJECT_ID=project-e0ad10c9-0b2f-4dc0-ac6` in `.env`, ADC already present). Before running anything through the bare `repoguard` command, `pip show repoguard`'s "Editable project location" must say this checkout, not a sibling worktree (Session 27 pitfall, `AGENTS.md §9`).
9. `claude/eager-gauss-ifyd8w` is superseded (Session 24) — delete it whenever convenient, nothing in it is unmerged real work. If a new session gets assigned that branch name again by the harness, don't assume its history is relevant; diff it against `main` first.