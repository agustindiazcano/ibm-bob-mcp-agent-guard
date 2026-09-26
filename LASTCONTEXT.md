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

### Session 7 — Phase 13: Dockerfile + CI/CD workflows + GCP deploy doc

All Claude-side Phase 13 deliverables written on `feat/13-dockerize` (rebased
on top of the still-unmerged `docs/claude-authors-code-and-cicd-plan`, to
avoid duplicating the Phase 13 table it already added to `PENDING.md`).

| # | Action | Files affected |
|---|---|---|
| 1 | `Dockerfile` — python:3.11-slim, installs the package, bundles `demo-repo/` so the deployed URL has something real to analyze immediately | `Dockerfile` |
| 2 | `.dockerignore` — excludes `.git`, `.bob/`, `bob-evidence/`, docs, caches, and every `repoguard-out/`/coverage artifact pattern | `.dockerignore` |
| 3 | Cloud Run port binding handled in the image's `CMD` (`--host 0.0.0.0 --port ${PORT:-8080}`) rather than changing `cli.py`'s locally-safe defaults | `Dockerfile` |
| 4 | `.github/workflows/ci.yml` — phase0/phase7 verify, demo-repo pytest, `repoguard gate demo-repo --threshold 60` (fast job) + `phase3` mutation determinism (separate slower job) | `.github/workflows/ci.yml` |
| 5 | `.github/workflows/cd.yml` — build image → push to Artifact Registry → `deploy-cloudrun` action, on push to `main` or manual dispatch | `.github/workflows/cd.yml` |
| 6 | `docs/DEPLOY.md` — full one-time GCP setup a human must run (project, APIs, Artifact Registry, service account + IAM roles, GitHub secrets/variables) | `docs/DEPLOY.md` |
| 7 | Marked all Phase 13 rows 🟢 in `PENDING.md`, with an honest note on what was and wasn't actually verified | `PENDING.md` |

### Key decisions (Session 7)

- **`docker build` itself is unverified** — this sandbox has no reachable Docker daemon (nested containerization blocked: `ulimit`/cgroup permission errors on `service docker start`). What *is* verified: the exact command the image's `CMD` runs (`repoguard serve --host 0.0.0.0 --port $PORT`) was run directly and confirmed serving, and `repoguard gate demo-repo --threshold 60` — the CI job's real check — passed for real (65.1% ≥ 60%). Both workflow YAMLs parse. The actual image build should happen once in CI (which has Docker) before anyone trusts it fully.
- Threshold set to 60, not the 80 in `RUNBOOK.md`'s old sketch — the real measured baseline is 65.1%, so 80 would fail CI immediately on unrelated work; 60 catches a real regression without being permanently red.
- Chose a static service-account-key secret over Workload Identity Federation for the GCP auth — faster to set up before a hackathon deadline; `docs/DEPLOY.md` flags WIF as the follow-up hardening step.
- `--allow-unauthenticated` on the Cloud Run deploy — a judge should never hit a login wall; flagged in `docs/DEPLOY.md` as a thing to revisit if the deployment outlives the hackathon.

### Session 8 — Wrote the missing reference tests; README "After" column is real now

PR #7 and #8/#9 confirmed merged to `main` (PR #8 had landed on the wrong base
branch — opened a follow-up PR #9 to actually get it onto `main`; see prior
session). With Docker/CI-CD in place, moved to the other standalone gap:
`docs/expected-after-tests/*.py` was documented as the demo's Plan B but the
four files never existed.

Wrote all four, ran them for real, then iterated on the surviving mutants
rather than accepting the first number: for each of the initial 14 survivors,
diffed the actual mutated source against the original to see exactly which
line changed, not just its category. That turned up 3 genuinely closeable
gaps (a `price < 0` / `stock < 0` boundary never tested at exactly 0, an
`is_member` default never exercised by omission, and two `raise` statements
whose custom exception message was never asserted — only their type, so a
`raise -> pass` mutant survived by relying on Python's own dict lookup
raising the same exception type incidentally). Fixed all three with targeted
boundary/message assertions, taking the mutation score from 82.28% -> 88.61%
-> 89.87% (71/79) across three re-measurements.

The 8 remaining survivors are true equivalent mutants, confirmed by reading
their diffs, not assumed: an `is_member` field `api.py` accepts but never
reads (dead code — fixing it would mean changing source to use it, which is
out of scope and arguably a separate real-bug report, not a test gap), and 7
`round(x, 2) -> round(x, 3)` mutations across `pricing.py`/`cart.py`/`api.py`
— exactly the pitfall AGENTS.md §9 already names as unkillable without
fragile float-precision tests.

Also caught and fixed a pre-existing, unrelated doc error while measuring
endpoint coverage: `api.py` has 7 endpoints, not the 8 documented in
`README.md` and `AGENTS.md`'s directory trees and old baseline table.

| # | Action | Files affected |
|---|---|---|
| 1 | Wrote `test_pricing_complete.py`, `test_cart_complete.py`, `test_inventory_complete.py`, `test_api_complete.py` | `docs/expected-after-tests/` |
| 2 | Measured, diffed survivors, strengthened 3 tests (boundary + exception-message assertions), re-measured to a stable 89.87% (71/79), confirmed deterministic across 2 runs | same 3 files |
| 3 | Copied into `demo-repo/tests/` to measure, removed again afterward — never left in place, per AGENTS.md §7 | (temporary only) |
| 4 | Updated `AGENTS.md §7`'s "After" row with the real numbers | `AGENTS.md` |
| 5 | Updated README's before/after table, prose, and endpoint count (8 -> 7) | `README.md` |
| 6 | Corrected the same endpoint-count error in `AGENTS.md`'s directory tree | `AGENTS.md` |
| 7 | Marked the reference-tests task done in `PENDING.md`; bumped README's Phase 12 status to 🟢 | `PENDING.md` |

### Key decisions (Session 8)

- Never accepted "equivalent mutant" as an excuse without checking first — every one of the original 14 survivors was diffed against its unmutated source to see the exact line, not just trusted by category. Only called something equivalent after confirming the mutated behavior is genuinely unobservable from outside (dead code) or matches an already-documented pitfall (round precision).
- The `is_member` dead-code finding is a real product gap (a field accepted but never used to affect pricing) — flagged here rather than "fixed" by changing `api.py`, since that would be a source change outside this task's scope and AGENTS.md reserves source changes for evidence of a real bug, decided deliberately, not slipped in while writing tests.

---

### Session 9 — Real results badges (fixed a fictional chart script)

`docs/make_results_chart.py` printed a hardcoded ASCII chart with fictional
numbers (30/0/3 → 85/72/22) that never came from a real measurement, and
`docs/img/results-en-{light,dark}.png` — referenced by the README badge —
never existed. Rewrote it to render real matplotlib bar charts from the
actual `AGENTS.md §7` numbers (65.1%→100% coverage, 20.25%→89.87% mutation).
`matplotlib` was named in `AGENTS.md §3`'s tech stack but never in
`pyproject.toml` — added as a `project.optional-dependencies` `docs` extra
(not a core dependency, since the CLI/MCP server never import it).

### Session 10 — Bob hit a blocked start; full audit found the real causes

Bob's Phase 11 swarm run failed at Sub-Task 1 with a FastAPI/starlette
error. Investigated rather than assumed: `git log` confirmed the unpinned
`fastapi>=0.111` line predates this session entirely — not something
introduced here. Root cause: no upper bound on `fastapi`, no `starlette`
pin, no lockfile, so different environments could resolve incompatible
pairs. Pinned both to the verified-working `fastapi==0.141.1`/
`starlette==1.7.0` (PR #13).

That fix exposed the deeper problem: I had only ever verified things in my
own sandbox venv, never checked whether the same code held up against
Bob's actual environment. Ran a full audit from a genuinely clean venv with
*no manual PATH manipulation* — the same conditions Bob runs under — and
found two real, previously undiscovered bugs, both worse than a crash
because they produce plausible wrong numbers instead of failing loudly:

1. `core.py`'s `measure_coverage()`/`_run_mutant()` called
   `subprocess.run(["pytest", ...])` with a bare command name, resolved via
   ambient PATH rather than the interpreter actually running
   `repoguard_engine`. Silently returned fabricated `0%`/`0`/`0` instead of
   erroring when PATH resolved to the wrong (or no) pytest.
2. `scripts/verify.py`'s `phase3`/`phase7` had the identical bug with bare
   `"python"` — reproduced live: `phase3` reported a false **PASS** with
   mutation score **100% (79/79 killed)**, because both runs hit the same
   broken interpreter and "two runs agree" trivially held for two wrong
   answers.

Fixed both with `sys.executable` (PR #14), except `phase0`'s intentional
bare `repoguard` check (deliberately tests PATH visibility, matching
`.bob/mcp.json`). Hardened `phase3` to also assert against the documented
baseline (`killed=16, total=79`), not just internal two-run agreement.
Also found and fixed `check_accessibility()`: `axe-playwright-python` was
imported but never declared as a dependency, so the check has likely never
actually run — it silently returned "0 violations," indistinguishable from
a real clean pass. Now declared, and reports `ok=False` with a real error
when it can't run.

Everything re-verified from the clean venv with zero PATH tricks: `phase3`
and `phase7` PASS with real numbers, demo-repo's suite, `repoguard
analyze/gate/serve`, and the MCP tools (called through the real `fastmcp`
`Client` protocol, not just imported) all confirmed working.

### Key decisions (Session 10)

- **"Passes in my sandbox" was quietly being treated as equivalent to "passes for Bob," and it isn't** — the fastapi/starlette break and the two PATH bugs it led me to find all stem from the same root gap: nothing had ever been verified from a clean environment with no manual PATH help. That's now been done once, thoroughly; it should become a standing check before claiming anything is "green," not a one-off.
- Didn't just fix the immediate fastapi/starlette error and stop — since the trigger was "code that depends on ambient environment state," searched for every other instance of that pattern (`grep` for bare `subprocess.run(["pytest"...`/`["python"...`) rather than assuming it was isolated.
- A verification script reporting PASS is not proof by itself — `phase3`'s own false 100% PASS is now a permanent cautionary example baked into `AGENTS.md §9`.

---

### Session 11 — watsonx.ai narrative summary (PR #18)

A separate session (not documented here at the time) added
`repoguard_engine/narrative.py`: an optional, advisory-only watsonx.ai prose
summary of an already-measured dashboard, wired as a 9th MCP tool
(`tool_generate_summary`) and a `repoguard analyze --summarize` CLI flag.
Merged to `main` as PR #18 before the session below started; found already
in place when that session pulled `main` mid-task. See `PENDING.md` Phase 15
and `docs/WATSONX_SETUP.md`.

### Session 12 — IBM Bob retired; watsonx.ai fix-loop orchestrator built

The user reported IBM Bob is no longer available and asked for a full
replacement using watsonx.ai directly (not Bob, not Watson Assistant). This
session discovered PR #18 (Session 11, above) mid-task via `git pull` and
reconciled scope with it before proceeding — kept `narrative.py` as-is,
built the fix loop as a separate, larger piece.

Built `repoguard_engine/watson_agent/` (`client.py`, `tools.py`, `prompts.py`,
`orchestrator.py`) as the functional replacement for `.bob/custom_modes.yaml`'s
Orchestrator/Test Writer/Critic/Gate/Publisher modes: one in-process loop
(not parallel subagents) that measures a real baseline, asks watsonx.ai to
write a test per prioritized file through a hard-guarded `write_test_file`
tool (rejects any path outside `tests/` — a tool property, not a prompt
rule), asks watsonx.ai to critique it, re-measures for real, and optionally
publishes a PR. Wired `repoguard fix` to it for real (previously a stub that
only printed instructions to use Bob).

Per explicit user instruction, `.bob/` was **not deleted** — it's left on
disk as inert legacy (a single new `.bob/DEPRECATED.md` marks it retired;
`BOBREADME.md` and `bob-evidence/` are the same kind of leftover). Nothing
new depends on any of it.

Caught one real bug via testing before it shipped: `run_fix_loop()`
originally called `get_chat_model()` (the credentials check) *after* the
multi-minute mutation baseline instead of before — a missing-credentials
failure would have taken several minutes instead of being instant. Fixed by
reordering; confirmed instant failure afterward with `PYTHONIOENCODING=utf-8
repoguard fix demo-repo` and no `WATSONX_*` env vars set (a separate,
pre-existing Windows console Unicode-rendering issue in `gate`/`fix`'s
`✗` output is unrelated to this change and out of scope).

| # | Action | Files affected |
|---|---|---|
| 1 | Built `repoguard_engine/watson_agent/` (client, tools, prompts, orchestrator) | new package |
| 2 | Wired `repoguard fix --publish --threshold` to the real orchestrator | `repoguard_engine/cli.py` |
| 3 | Added `.bob/DEPRECATED.md`; left the rest of `.bob/` untouched | `.bob/DEPRECATED.md` |
| 4 | Added `scripts/verify.py phase16` (write-guard + fail-loud credential check); extended `phase7`'s tool list to 9 | `scripts/verify.py` |
| 5 | Rewrote Bob-specific sections in `README.md`, `RUNBOOK.md`, `docs/ARCHITECTURE.md`, `docs/DEMO.md` for watsonx.ai; dropped the dated hackathon footer | those files |
| 6 | Renamed `docs/AI_ASSITED_DEVELOPMENT_FRAMEWORK_BOB.md` → `docs/AI_ASSISTED_DEVELOPMENT_FRAMEWORK.md`, rewritten for Claude-as-builder | `docs/` |
| 7 | Updated `AGENTS.md` **and `CLAUDE.md` identically** (§2, §3, §5, §6, §8, §9, §11) — a sync rule discovered mid-task that wasn't being followed before this change | both files |
| 8 | Re-scoped `PENDING.md` Phases 7/8/9/11/14, flagged the repo-rename decision as a separate open item | `PENDING.md` |
| 9 | Carried forward stray pre-existing WIP from before this session (verify.py's phase3 timeout 270→600s) that had never been committed | `scripts/verify.py` |

### Key decisions (Session 12)

- `.bob/` is legacy, not deleted — the user's explicit call, overriding the
  original plan (which would have removed it). `bob-evidence/`, `BOBREADME.md`
  get the same treatment: left alone, documented as inert.
- The MCP server (`mcp_server.py`, `repoguard mcp`) was never actually
  Bob-specific — it's a generic protocol server. Kept as-is, just no longer
  described as "the Bob integration" in docs.
- `watson_agent/` calls `pipeline`/`core`/`api_check` directly (in-process),
  not through an MCP round-trip — same layering `web/server.py` already uses.
- Live tool-calling with real watsonx.ai credentials is unverified — no IBM
  Cloud account available here, same gap already flagged for `narrative.py`
  in Session 11/PR #18. `ModelInference.chat()`'s signature and response
  shape were confirmed against the real installed SDK (`inspect.signature`/
  `help()`), same rigor as that PR used.

---

### Session 13 — Phase 14 frontend: Next.js dashboard scaffold (`feat/14-nextjs-dashboard`)

Built `web-next/` per `docs/ARCHITECTURE-front.md`'s plan and `PENDING-front.md`'s
backend-gap tracker — both kept as satellite files, separate from
`PENDING.md`/`docs/ARCHITECTURE.md`, on purpose, so this frontend branch
doesn't fight a backend branch over the same Phase 14 section (folds back at
merge time, per that file's own header note).

Scaffolded a Next.js App Router app with a single route: `RepoForm` +
`ActionBar` drive `/api/analyze` and `/api/stream`; `StreamLog` renders the
SSE events verbatim; `StatCards`/`GapsList`/`RiskTable` render
`AnalyzeResponse` fields verbatim, no client-side reinterpretation of any
number (`AGENTS.md §4`). Autofix ships disabled (backend gap 3: no
`POST /api/fix` yet); `SummaryPanel` is not built (backend gaps 4/6: needs a
summary endpoint and AI-provider labeling, which in turn wait on Phase 16's
`ai_providers.get_provider()` — that folder correctly still doesn't exist).

| # | Action | Files affected |
|---|---|---|
| 1 | Scaffolded `web-next/` (Next.js App Router, TypeScript, ESLint) | `web-next/` (new) |
| 2 | Built `RepoForm`, `ActionBar` (Analyze + Gate wired to `/api/analyze`, Autofix disabled), `StreamLog`, `StatCards`, `GapsList`, `RiskTable` | `web-next/app/components/` |
| 3 | Wired `app/lib/api.ts` (`fetchAnalyze`, `streamUrl`) against `NEXT_PUBLIC_REPOGUARD_API_BASE` | `web-next/app/lib/` |
| 4 | Verified `npm run lint`, `npm run build`, and a real `next dev` serve (200, title "TestMind AI") | — |
| 5 | Committed and pushed (`27c5a52`) to `feat/14-nextjs-dashboard` | — |
| 6 | Updated `PENDING-front.md` deliverable statuses to match what's actually built; added this session entry | `PENDING-front.md`, `LASTCONTEXT.md` |

### Key decisions (Session 13)

- **Gate reuses `/api/analyze`**, not a separate endpoint — matches gap 2's
  note that `/api/analyze?gate_threshold=N` already returns `passed_gate`,
  so no new backend work was needed for that button.
- **Didn't work around the missing CORS middleware from this branch** — it's
  explicitly gap 1, owned by the backend, already being fixed on a separate
  branch (`fix/web-cors`). End-to-end fetch against a real running
  `repoguard serve` is therefore unverified here on purpose, not an oversight.
- **`PENDING-front.md` / `docs/ARCHITECTURE-front.md` stay satellite files**,
  not folded into `PENDING.md` / `docs/ARCHITECTURE.md` — that fold is
  explicitly a merge-time step per the file's own header, not a per-session one.

---

### Session 14 — Summary endpoint + SummaryPanel (two parallel sessions, PRs #26/#27)

Ran as two Claude Code sessions in parallel: backend on
`feat/14-summary-endpoint` (this checkout), frontend on
`feat/14-summary-panel` (separate `-frontend` worktree). The contract was agreed
up front so neither had to wait: `POST /api/summary`, body = `/api/analyze`'s
dashboard, response `{ok, text, error, provider}`. No shared files touched;
both merged to `main`.

| # | Action | Files affected |
|---|---|---|
| 1 | `POST /api/summary` wraps `narrative.generate_summary()`; `provider` fixed to `"watsonx.ai"` at the endpoint, `NarrativeResult` unchanged (MCP/CLI callers untouched) | `repoguard_engine/web/server.py` |
| 2 | CORS `allow_methods` → `["GET", "POST"]` | `repoguard_engine/web/server.py` |
| 3 | `/api/stream` takes `gate_threshold` (default 80.0) instead of a hardcoded 80% | `repoguard_engine/web/server.py` |
| 4 | `api_summary` changed from `async def` to `def` — caught in the frontend session's review | `repoguard_engine/web/server.py` |
| 5 | `SummaryPanel`, `fetchSummary()`, `SummaryResponse` type (frontend session) | `web-next/app/` |
| 6 | Gaps 4/5 closed, gap 6 partially, `SummaryPanel` 🟢 | `PENDING-front.md` |

### Key decisions (Session 14)

- **Blocking calls in FastAPI handlers must be plain `def`.** `generate_summary()`
  can take up to 30s with real credentials; as `async def` it would freeze the
  event loop, and `/api/stream` would stop sending progress. It never showed up
  in testing, because with no credentials it returns in milliseconds.
- `provider` is added in the web layer, not in `narrative.py` — once
  `ChatProvider` exists, it becomes the source of that field.
- Verified: phase0/phase7 PASS; `/api/stream` gives `passed_gate: true` at
  threshold 60 and `false` at the default 80 against demo-repo (65.1%);
  `/api/summary` returns the credentials error with no `WATSONX_*` set.
- `repoguard serve` on this Windows machine needs `PYTHONIOENCODING=utf-8`
  (the pre-existing `→` console-encoding crash); `GET /` returned 500 during
  testing — not investigated, backlog.

### Session 15 — E2E verified, two web-server bugs fixed, PENDING-front.md folded

| # | Action | Branch / files |
|---|---|---|
| 1 | Frontend session ran the browser E2E on `main` (`50fe2e6`): Playwright + `repoguard serve` + `next dev`, all three endpoints 200, `SummaryPanel` showed the credentials error, dashboard intact | — |
| 2 | `GET /` 500 on Windows: `index.html` read as cp1252. Fixed with explicit `encoding="utf-8"`, plus the same latent bug in `api_check.py` (2 reads) and `core.py` (2 reads) that would break on any non-ASCII source | `fix/web-root-encoding` |
| 3 | `/api/stream` frozen at the first progress event: `api_analyze` was `async def` running `run_pipeline()` synchronously, and `web-next` opens both at once. Now `def`; confirmed stream events arrive while analyze is still running | `fix/web-root-encoding` |
| 3b | Flagged by the frontend session: the two concurrent requests ran pytest-cov with `.coverage`/`coverage.json` at fixed paths in the target repo. `measure_coverage()` now uses a per-run temp dir (`COVERAGE_FILE` + `--cov-report=json:<tmp>`); 1 and 4 parallel runs all 65.12% | `fix/web-root-encoding` |
| 3c | Frontend session fixed the double `POST /api/summary` under `next dev` | `fix/14-summary-double-post` |
| 4 | Folded `PENDING-front.md` into `PENDING.md` Phase 14 (gaps, deliverables, verified, known issues), deleted it, repointed references | `docs/14-fold-pending-front` |

### Key decisions (Session 15)

- **Rule for `web/server.py`: any handler that calls blocking engine code
  must be `def`, not `async def`.** Two instances in two sessions
  (`api_summary`, `api_analyze`); only `_stream_pipeline` is legitimately async
  (it offloads coverage with `run_in_executor`).
- Engine change → ran §7: phase0/phase3/phase7 PASS (mutation 20.25%, 16/79
  on both runs), demo-repo 5 passed, coverage 65.1%, 4 gap files.
- Not changed: `ci.yml`/`cd.yml` still list `PENDING-front.md` in
  `paths-ignore` — harmless now that the file is gone; clean up whenever CI is
  touched next. `docs/ARCHITECTURE-front.md` is not folded yet (still a Phase
  14 Docs deliverable).

---

## Current repo state

- Branch: `main` at `7480cb0`; open, independent branches: `fix/web-root-encoding` (backend), `fix/14-summary-double-post` (frontend), `docs/14-fold-pending-front` (docs)
- Phase 0: 🟢 · Phase 3: 🟢 · Phase 7: 🟢 · Phase 8: 🟢 (redefined for watsonx.ai) · Phase 9: 🟢 (`repoguard fix` now real) · Phase 13: 🟢 · Phase 15: 🟢 (narrative, PR #18)
- Phase 14: 🟡 — all dashboard components including `SummaryPanel` merged and verified end-to-end in a browser (see `PENDING.md` Phase 14); remaining: Autofix (gap 3, no `POST /api/fix`), Vercel deploy, folding `docs/ARCHITECTURE-front.md` into `docs/ARCHITECTURE.md`, and the `ok=true` summary path (needs credentials)
- IBM Bob is retired. `.bob/` stays on disk as inert legacy (`.bob/DEPRECATED.md`); `repoguard_engine/watson_agent/` is the live replacement.
- Remaining 🔴 critical-path item: Phase 11, a real end-to-end `repoguard fix` run against `demo-repo` with actual IBM Cloud credentials — same human-gated situation as GCP deploy, not something any agent here can supply
- GCP deploy still pending a human running `docs/DEPLOY.md`'s one-time setup
- Open, not yet decided: whether to rename the GitHub repo/local directory (`ibm-bob-mcp-agent-guard`) now that Bob is gone — flagged in `PENDING.md`, deliberately not done here

---

## How to resume

1. Read `PENDING.md` for the task list (Phase 14 now holds the frontend tracker too).
2. Run `python scripts/verify.py phase0`, `phase3`, `phase7`, `phase15`, `phase16` to confirm baseline holds.
3. For the frontend: CORS and `/api/summary` are on `main`; run `PYTHONIOENCODING=utf-8 repoguard serve` + `npm run dev` (with `NEXT_PUBLIC_REPOGUARD_API_BASE`) for the still-pending browser end-to-end check.
4. Get real IBM Cloud credentials (`docs/WATSONX_SETUP.md`) and run `repoguard fix demo-repo` for the first live Phase 11 run — that's the one thing no agent session here can do without a human providing an account.
5. GCP setup (`docs/DEPLOY.md`) is the other remaining human-only task — do it whenever, it doesn't block anything else.
6. The repo-rename decision (`ibm-bob-mcp-agent-guard`) is open and low-urgency — decide whenever, it's cosmetic.
