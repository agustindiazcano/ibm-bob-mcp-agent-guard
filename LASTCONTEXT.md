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

### Session 16 — Phase 17 design: measurement history on Postgres + Terraform (`claude/eager-gauss-ifyd8w`)

| # | Action | Files affected |
|---|---|---|
| 1 | Wrote the design for storing every measured run: ER schema, SQL views, risk-model calibration plan, six dashboard charts, API routes, Terraform layout for GCP, two-day build order with an explicit cut line | `docs/DATA_PLATFORM.md` |
| 2 | Added Phase 17 tracker | `PENDING.md` |
| 3 | README: new sections + ToC entries for CI/CD, Deploy to Google Cloud, Database (planned), Infrastructure as code (planned); `DEPLOY.md`, `DATA_PLATFORM.md`, `ARCHITECTURE-front.md` added to Documentation; `.github/workflows/`, `Dockerfile`, both docs added to the tree. All anchors checked against GitHub slug rules | `README.md` |
| 4 | Corrected two false claims: risk score described as `complexity × churn × (1 − detection)` (README, PENDING Phase 4) — real formula is `uncovered / non-blank lines`; `git` listed as used for churn and cloning by URL — neither exists, only `repoguard fix` uses git (branch/commit/push) | `README.md`, `PENDING.md` |

Key decisions (design only, nothing built):
- Database stores, engine measures: all derived values (deltas, trends) are SQL views, never stored columns. Persistence is off unless `REPOGUARD_DATABASE_URL` is set.
- Justification for a DB: Cloud Run's filesystem is ephemeral, so `repoguard-out/` history can't survive on the deployed service.
- Engine gaps found while designing: `run_mutation` discards per-mutant outcomes (only positional surviving IDs kept), and per-test outcomes are never recorded. Both are needed before the schema can hold anything useful (block A2).
- `compute_risk` today is `uncovered / non-blank lines` only; `PENDING.md` Phase 4's `complexity × churn × (1 − detection)` description doesn't match the code. Phase 17 proposes calibrating extra terms against stored survival data rather than adding them by assertion.
- Terraform covers the backend only; the frontend stays on Vercel (Phase 14's decision stands). CD moves to Workload Identity Federation.

---

### Session 17 — Phase 18 design: multi-agent swarm (`claude/eager-gauss-ifyd8w`)

| # | Action | Files affected |
|---|---|---|
| 1 | Wrote the plan to bring back a parallel multi-agent swarm: Bob's 9 modes mapped to new agents, lanes per file (Writer → Verifier → Critic), two levels of parallelism, file contract, build order, verification incl. a credential-free stub E2E | `docs/MULTI_AGENT_SWARM.md` |
| 2 | README: new "Multi-agent swarm (planned)" section + ToC entry, Documentation link, tech-stack row, pointer from "Is it multi-agent?" | `README.md` |
| 3 | Phase 18 tracker | `PENDING.md` |

Found while designing (not fixed, planned as S1/§3 of the doc):
- `run_mutation(paths_to_mutate=<file>)` silently finds 0 mutants (`rglob` on a file path returns nothing) and returns `total = 0` instead of an error.
- Today's fix loop gives each writer the whole repo's surviving mutant IDs as bare integers (no descriptions), never picks a fully covered file that still has surviving mutants (risk = coverage gap only), caps at 3 files (demo-repo has 4 modules), and its critic has the same write tool as the writer.
- Measured: sequential mutation on demo-repo, 79 mutants in 53 s (this container) — the H1 baseline at the engine level.

---

### Session 18 — Phase 16 Stage A+B (multicloud AI) + Phase 13 Cloud Run deploy via WIF (`feat/16-ai-providers`, PR #37, merged)

| # | Action | Files affected |
|---|---|---|
| 1 | Extracted `ChatProvider` abstraction (`ai_providers/base.py`); moved `watson_agent/client.py`'s watsonx.ai logic to `ai_providers/watsonx.py`; `get_provider()` reads `REPOGUARD_AI_PROVIDER` (default `watsonx`) | `ai_providers/__init__.py`, `base.py`, `watsonx.py`; `watson_agent/client.py` deleted |
| 2 | `narrative.py` and `watson_agent/orchestrator.py` switched to `get_provider().chat()`; `--provider` flag added to `repoguard fix` / `analyze --summarize` | `narrative.py`, `orchestrator.py`, `cli.py` |
| 3 | Implemented `ai_providers/vertex.py` against real `google-genai==2.25.0`; live-verified against a real GCP project (`gemini-2.5-flash`, `us-central1`): plain text call + full tool-calling round trip both work | `ai_providers/vertex.py`, `docs/VERTEX_SETUP.md` |
| 4 | Fixed 2 real integrity bugs found via that live testing: (a) orchestrator tool dispatch only caught `SourceEditRejected`, so a hallucinated tool path crashed the whole fix loop with a raw exception; (b) `run_mutation()` never checked the unmutated baseline passes first, so a broken AI-written test suite could report a false 100% mutation score | `orchestrator.py`, `core.py` |
| 5 | Cloud Run deploy via Workload Identity Federation, done early (better than the static-key path originally planned). Created for real against `project-e0ad10c9-0b2f-4dc0-ac6`: Artifact Registry repo, `repoguard-deployer` service account + IAM roles, WIF pool/provider scoped to this repo. `cd.yml` switched from `GCP_SA_KEY` to WIF — no long-lived GCP secret in GitHub | `.github/workflows/cd.yml`, `docs/DEPLOY.md` |
| 6 | `web-next/` deployed to Vercel (https://ibm-bob-mcp-agent-guard.vercel.app/); `NEXT_PUBLIC_REPOGUARD_API_BASE` still a `localhost` placeholder until the Cloud Run URL exists | — |
| 7 | Docs updated to match, PR opened and merged | `PENDING.md`, `README.md`, `AGENTS.md`+`CLAUDE.md`, `docs/MULTICLOUD_AI.md`, `docs/ARCHITECTURE.md`, `docs/DATA_PLATFORM.md` |
| 8 | Found `PENDING.md` Phase 16 was left stale by the merged PR itself (`vertex.py` still shown 🔴 "needs real GCP credentials" after it had already been built and live-verified in the same PR) — corrected, plus this session log entry | `PENDING.md`, `LASTCONTEXT.md` |

Verified before/after merge: `verify.py multicloud` PASS, `verify.py phase16` PASS, `verify.py phase3` PASS (20.25%, 16/79, both runs — unaffected by the `run_mutation` baseline-check fix).

Key findings:
- Real watsonx.ai credentials were used this session; the default tool-calling model (`llama-3-3-70b-instruct`) hits free-tier `429`s under load, and the fallback (`mistral-small-3-1-24b-instruct-2503`) doesn't reliably call tools — a real `repoguard fix demo-repo` run with watsonx produced zero mutation-score improvement. This is what motivated Vertex as the more reliable provider, not just a diversification goal.
- Both cloud providers now have real, live-verified credentials configured — the remaining Phase 11 blocker is model tool-calling reliability, not credential availability (see below).

---

### Session 19 — doc fixes (PR #38) + Phase 17 Block B1: Terraform for the WIF identity (PR #39, both merged)

| # | Action | Files affected |
|---|---|---|
| 1 | Fixed `PENDING.md`'s stale Phase 16 status (`vertex.py` still shown 🔴 after PR #37 had already built and live-verified it); logged Session 18 in `LASTCONTEXT.md` | `PENDING.md`, `LASTCONTEXT.md` (PR #38) |
| 2 | User pointed at a pattern from another project (WIF pool + scoped deployer SA + minimal roles, managed in Terraform) and asked for the same approach here | — |
| 3 | Wrote `infra/terraform/` codifying Phase 13's already-existing identity: `github-pool`/`github-provider`, `repoguard-deployer` SA + its 3 project IAM roles, the Artifact Registry repo, 4 enabled APIs | `infra/terraform/{versions,variables,cicd,outputs}.tf`, `README.md` |
| 4 | Ran `terraform import` for all 10 resources against the real project, then `terraform plan` → **"No changes. Your infrastructure matches the configuration."** Outputs match `docs/DEPLOY.md`'s documented `WIF_PROVIDER`/`DEPLOYER_SA` exactly. No `apply` run; state is local and gitignored | — |
| 5 | Added `infra-ci.yml` (fmt/validate only, no credentials); pointed `docs/DEPLOY.md` at the Terraform-managed setup, kept original `gcloud` commands as historical record; `PENDING.md` Phase 17 B1 → 🟢; `AGENTS.md`/`CLAUDE.md` tree updated (kept identical) | `docs/DEPLOY.md`, `PENDING.md`, `AGENTS.md`+`CLAUDE.md`, `.github/workflows/infra-ci.yml` |

Deliberately deferred, not done here: the 3 project-level IAM roles on `repoguard-deployer` are broader than needed (project-wide, not scoped to this one AR repo + this one Cloud Run service, unlike the other project's pattern) — noted in `infra/terraform/README.md` as a real permissions change against a live project, left for its own PR rather than bundled in silently.

---

### Session 20 — Phase 11 done for real (PR #41, #42 merged; Gemini-3 work not yet a PR) + Phase 17/18 planning kickoff

| # | Action | Files affected |
|---|---|---|
| 1 | First real Cloud Run deploy: `GCP_PROJECT_ID` repo variable had a leading space, breaking the Docker tag. Hardened `cd.yml` to trim + validate all 6 repo variables and fail loud instead of a cryptic Docker error. Deploy then succeeded for real (`https://repoguard-ljm5hefnsq-uc.a.run.app`, confirmed `GET /api/analyze` returns real 65.1% coverage) | `.github/workflows/cd.yml` (PR #41) |
| 2 | `repoguard fix`'s CLI crashed with a raw traceback when `run_mutation()`'s baseline guard correctly raised `RuntimeError` on a broken AI-written suite — now caught and reported cleanly (exit 1, no traceback), same pattern as `gate`'s failure message | `repoguard_engine/cli.py` (PR #42) |
| 3 | Phase 11, 3 real attempts, 3 real bugs, then success: (a) `gemini-2.5-flash` twice hallucinated `Inventory.clear()` (doesn't exist) — caught by the baseline guard but the loop had no way to self-correct; (b) moved to Gemini 3 (`gemini-3.8-flash`, `location=global` — 404s at `us-central1`) and added a `run_tests` tool + prompt changes requiring the writer/critic to actually execute pytest before finalizing; (c) Gemini 3's function-call parts carry a `thought_signature` that must be replayed next turn or the API 400s — `vertex.py` was discarding it, now captured and replayed. Final real result: **20.25% (16/79) → 89.87% (71/79)**, coverage 65.1% → 99.1%, independently re-measured, exact match | `repoguard_engine/ai_providers/vertex.py`, `watson_agent/tools.py`, `watson_agent/prompts.py`, `watson_agent/orchestrator.py`, `docs/VERTEX_SETUP.md`, `docs/MULTICLOUD_AI.md`, `PENDING.md` — branch `feat/11-gemini3-antihallucination`, not yet a PR |
| 4 | Kicked off Phase 17 Block A (DB store) and Phase 18 (swarm) planning in parallel, via isolated-worktree Opus subagents — read-only, no code written. DB plan found ~15 real gaps in `docs/DATA_PLATFORM.md` vs. actual code (rounding, SQLite view portability, import cycles, cross-OS fingerprint paths, an unauthenticated `persist=true` write-amplification risk, etc.); swarm plan found 4 more real bugs (missing `PYTHONDONTWRITEBYTECODE`, a baseline-vs-mutant-copy environment mismatch that reproduces the false-100% bug class one layer up, timeouts scored as kills, a stale MCP docstring) and the hard limit that demo-repo's 71/79 ceiling means the swarm can only tie H2, never beat it, on this fixture | both folded into the docs for real: `docs/DATA_PLATFORM.md` §13 (step-by-step Block A plan + 6 decisions) and `docs/MULTI_AGENT_SWARM.md` §14 (S0–S8 plan + 15 risks), corrections applied inline throughout both docs — PR #46 |

Demo-repo's tests/ were restored to the documented weak baseline (5 passed, 65.1%, 20.25%/16/79) after each Phase 11 attempt, including the successful one — Phase 11's AI-written tests were real and passing but were never meant to permanently replace the baseline every other check and doc depends on, same rule as Plan B's reference tests.

### Session 21 — Frontend punch list: PR #48 (parallel), CORS + Vertex-on-Cloud-Run (PRs #49/#50, then a stray-commit chase)

Two sessions worked in parallel against a shared punch list the frontend
session produced (Vercel → real backend, `ok=true` summary, Autofix).

| # | Action | Files affected |
|---|---|---|
| 1 | Frontend session: clear "backend unreachable" error message + real production dashboard screenshots (light/dark) replacing placeholders | `web-next/app/lib/api.ts`, `README.md`, `docs/img/dashboard-{light,dark}.png` — PR #48, merged |
| 2 | `/api/analyze` 400-vs-500 fix (already logged) merged as PR #47; `cd.yml` auto-redeployed on the `main` push — confirmed live: bad `repo_path` now returns 400, not 500 | — |
| 3 | Punch-list item 3 (Vercel → real backend): `REPOGUARD_CORS_ORIGINS` set to the Vercel origin, applied live via `gcloud run services update`, confirmed with a real CORS preflight — PR #49, merged | `.github/workflows/cd.yml` |
| 4 | Punch-list item 4 (`ok=true` summary): found 3 real gaps live-testing `/api/summary` (independently confirmed by the frontend session too) — `REPOGUARD_AI_PROVIDER` unset (defaulted to watsonx), the deployed image missing `google-genai` (`Dockerfile` had no `[vertex]` extra), and the Cloud Run runtime SA missing `roles/aiplatform.user`. User ran the IAM grant by hand (blocked for an agent session — a permission grant, not something Claude Code's auto-mode classifier allows regardless of scope, even via Terraform apply, which would be "the same outcome through another tool") | — |
| 5 | **Real process mistake, three times in one session:** pushed the `Dockerfile`/docs fixes *after* the user had already merged the branch they were on (PR #47, then #49, then #51 each ate a trailing commit the same way). A merged PR is closed — new pushes to that branch name go nowhere until opened as a *new* PR, and "the CD run succeeded" doesn't mean *your* commit was in it if something merged out from under you mid-work. **Fix that actually stuck:** stop pushing incremental commits to a branch someone might merge at any moment; instead land all related commits locally first, push once, and treat that push as final rather than a checkpoint. Recovered the orphaned commits each time via `git merge origin/<old-branch>` into a fresh branch rather than losing the work | `LASTCONTEXT.md` (this entry) |
| 6 | While chasing the above as if it might be a real bug: `vertex.py`'s `except ImportError` caught *any* import failure under one fixed message, discarding the real inner exception — genuinely worth fixing regardless (a masked error is a real diagnosability gap), just not what was actually blocking this specific case. Reproduced `pip install -e ".[vertex]"` locally in a clean venv first, confirmed it installs and imports fine, before concluding the error had to be a deploy/config problem, not a dependency one | `repoguard_engine/ai_providers/vertex.py` |
| 7 | Doc staleness the frontend session flagged: `PENDING.md`'s Phase 14 "Vercel deploy" row still said `NEXT_PUBLIC_REPOGUARD_API_BASE` pointed at `localhost:8000`; `LASTCONTEXT.md` had nothing recorded past PR #44 | `PENDING.md`, `LASTCONTEXT.md` |
| 8 | **Success, verified live**: `POST /api/summary` against `https://repoguard-ljm5hefnsq-uc.a.run.app` returned `{"ok": true, "provider": "vertex", "text": "The test suite covers 65.1...% ..."}` — real generated prose matching the measured numbers, not fabricated. Punch-list item 4 is done | `PENDING.md` Phase 14 gap 8 |

Items 4-7's fixes landed as PR #52 (`fix/vertex-dockerfile-extra-final`,
after PR #51 dropped the actual `Dockerfile` change the same way #49 had —
see item 5). `main` at `1da4804` has everything.

**Real, measured chain of Cloud Run env-var changes this session** (all
via `gcloud run services update --update-env-vars`, each confirmed with a
real request before moving to the next): `REPOGUARD_CORS_ORIGINS` →
`VERTEX_PROJECT_ID` → `REPOGUARD_AI_PROVIDER=vertex`. Real IAM policy
confirms `roles/aiplatform.user` granted to
`993240087609-compute@developer.gserviceaccount.com`. **`ok: true`
re-verified live** against the real deployed service after PR #52 merged
and redeployed — the full punch-list item 4 chain is closed.

### Session 21-front — frontend side of the same punch list (parallel Opus session, worktree `ibm-bob-mcp-agent-guard-frontend`)

Only what Session 21 above doesn't already cover.

| # | Action | Files / PR |
|---|---|---|
| 1 | Frontend context docs brought up to date with `main` (real `/api/summary` contract, closed gaps, Vercel URL, 7 README lines still calling Vertex unbuilt) | PR #43 |
| 2 | Visual design: card layout, stat cards, gaps list, risk table with score bars (bar width = the engine's own 0–1 score), live-progress states, advisory-tagged summary, light/dark, mobile. CSS Modules, no new dependency | PR #44 |
| 3 | Non-2xx responses show FastAPI's `detail` (pairs with PR #47's 400 for a bad `repo_path`); over HTTP/2 `statusText` is empty, so the old fallback showed just "analyze failed: 400" | PR #50 |
| 4 | Verified the public demo live in Chrome (Vercel → Cloud Run): 3 calls 200 in ~6 s, 65.1% (112/172), 4 gap files, gate FAIL, bad path → "repo_path does not exist…", summary → "google-genai import failed" (the pending branch above) | `PENDING.md` Phase 14 "Verified live" |
| 5 | Found while verifying: Vercel kept serving stale builds. `NEXT_PUBLIC_*` is inlined at build time; a manual Redeploy of an *older* deployment became the newest Production build and shadowed #48/#50, and one Promote rolled back to a `127.0.0.1:8000` build. Rule: after changing a Vercel env var, Redeploy the **newest `main`** deployment; check which build is live by searching the served JS for the API URL | `PENDING.md` Phase 14 known issues, `docs/ARCHITECTURE-front.md`, `web-next/README.md` |

---

### Session 22 — Phase 14 gap 3: Autofix, `POST /api/fix` (`claude/eager-gauss-ifyd8w`)

The session started from a local branch 43 commits behind `origin/main`, so
the first "what's next" answer was built on stale context: it still treated
watsonx and IBM credentials as the blocker. The user caught it. Before
answering "what's next", run `git fetch` and read `LASTCONTEXT.md` from
`origin/main`.

| # | Action | Files affected |
|---|---|---|
| 1 | `run_fix_loop` gets an optional `on_event(type, data)` progress callback (baseline, per-file writer/critic, re-measure). It only reports progress and changes nothing; the CLI path is unchanged | `watson_agent/orchestrator.py` |
| 2 | Autofix over HTTP. Token gate: `REPOGUARD_FIX_TOKEN` unset → 503, missing/wrong bearer token → 401 (`hmac.compare_digest`). One run per process (409). The loop runs on a temp copy with `publish=False`; the copy is deleted afterwards and the written tests come back in the `done` event. Output streams as NDJSON from a worker thread, with a heartbeat every 15 s. The worker owns the lock, so a client disconnect still releases it | `web/fix_job.py` (new), `web/server.py` |
| 3 | `verify.py phase14fix`, credential-free with a stubbed `run_fix_loop`: covers 503/401/400/409, event order, the returned test file, deletion of the sandbox, and that `demo-repo/` stays byte-identical | `scripts/verify.py` |
| 4 | Frontend: Autofix button enabled; token entered in a password field and kept in React state only; `streamFix()` reads the NDJSON with `fetch` + `ReadableStream`, since `EventSource` can't POST or send headers; new `FixResultPanel` shows engine before → after, the tests written, and critic notes labeled advisory | `web-next/app/{page.tsx,lib/api.ts,lib/types.ts,components/*}` |
| 5 | Checked in real Chromium against `repoguard serve` + `next dev`, with the stubbed fix loop but real engine measurements on the copy. Button disabled with no token; wrong token shows "Missing or invalid Autofix token."; progress streamed mid-run, survived a 20 s silent gap, result panel rendered; `demo-repo/tests` unchanged and no sandbox left behind | — |
| 6 | Cloud Run `--timeout=1800` (default 300 s would cut a run off). Token setup documented as a human step: Secret Manager + `secretAccessor` for the runtime SA + `--update-secrets` | `.github/workflows/cd.yml`, `docs/DEPLOY.md` §5 |
| 7 | Docs | `PENDING.md`, `docs/ARCHITECTURE-front.md` (NDJSON contract; also corrected stale gap 8 row → 🟢), `docs/ARCHITECTURE.md`, `README.md`, `CLAUDE.md`+`AGENTS.md` |

Verified before commit: `verify.py` phase0/phase3/phase7/phase15/phase16/multicloud/phase14fix all PASS; `demo-repo` 5 passed; `repoguard analyze ./demo-repo --mutation` → 65.1%, 20.25% (16/79), 4 gap files — Section 7 baseline unchanged. `web-next` lint + build clean.

Not verified here: a live Autofix run. This container has no Vertex
credentials, and the Cloud Run token isn't attached yet. Gap 3 stays 🟡
until a real run from the Vercel demo shows a measured mutation score above
20.25%, and `/api/analyze` on the same service still reports 65.1% after it.

---

### Session 23 — Frontend gaps: endpoints card, honest mutation progress, Gate, `verify.py phase14ui` (`claude/eloquent-fermat-4e9gir`)

Frontend-only session, run in parallel with other agents on docs, the
database (Phase 17) and planning, so it stayed out of `core.py` and
`pipeline.py`. The only backend change is in `web/server.py`.

| # | Action | Files affected |
|---|---|---|
| 1 | `/api/analyze` returns `endpoints`: `run_pipeline` already ran `find_untested_endpoints`, and the route dropped the result. Added in `server.py`, not `build_dashboard_data`, so `/api/summary`'s input and `/api/fix`'s `before`/`after` are unchanged | `web/server.py` |
| 2 | New `EndpointsList` card: method + path, "tested"/"no test", "1 / 7 tested" on `demo-repo`. Footnote says "tested" is a static mention in a test file, not a request | `web-next/app/components/EndpointsList.tsx`, `Lists.module.css`, `lib/types.ts`, `page.tsx` |
| 3 | Bug: `/api/stream` was opened without `gate_threshold`, so at a 60% threshold the log said `passed_gate: false` while the gate card said PASS | `web-next/app/lib/api.ts`, `page.tsx` |
| 4 | Bug: with mutation on, the log's badge said "Done" as soon as the stream (coverage/gaps/risk only) ended, while `/api/analyze` kept running mutation. Now a "Running mutation testing" line with an elapsed clock stays active and the badge stays "Running" until the dashboard is in | `StreamLog.tsx`, `page.tsx` |
| 5 | Gate was a second Analyze button and ran mutation when the box was ticked. It now sends `mutation=false`, like `repoguard gate` | `ActionBar.tsx`, `page.tsx` |
| 6 | `verify.py phase14ui`: production build + real backend in Chromium via Python Playwright (no new dependency), no stubs. Checks rendered numbers against `/api/analyze` and against `AGENTS.md §7`, including a real mutation run (20.25%, 16 / 79). Against the previous frontend it FAILs on items 2 and 3 | `scripts/verify.py` |
| 7 | Docs: component table, `endpoints` contract, verification section, and the stale "summary still unavailable" paragraph in `ARCHITECTURE-front.md`; Phase 14 rows in `PENDING.md`; the tree's component line in `AGENTS.md`+`CLAUDE.md` | docs |

Verified: `verify.py phase14ui` PASS (mutation run 63 s here);
phase0/phase3/phase7/phase15/phase16/multicloud/phase14fix PASS; `demo-repo`
5 passed; `repoguard analyze ./demo-repo --mutation` → 65.1%, 20.25%
(16/79), 4 gap files. `web-next` lint + build clean. Checked by eye in
light, dark and at 390px.

In this container Playwright 1.63 didn't match the preinstalled Chromium
build, so the check was run with `REPOGUARD_CHROMIUM=/opt/pw-browsers/chromium`.

---

## Current repo state

- **Session 23 (frontend gaps) is on `claude/eloquent-fermat-4e9gir`, pushed, not merged.** Session 22's Autofix is on `main` (PR #55).
- Branch: `main` — PR #37 (Phase 16 + 13 WIF), #38 (doc fixes), #39 (Phase 17 B1 Terraform), #40 (session log), #41 (cd.yml trim fix), #42 (cli graceful failure), #43 (frontend context docs), #44 (dashboard visual design), #45 (Phase 11 Gemini 3 + `run_tests` + `thought_signature` fixes), #46 (Phase 17/18 planning corrections), #47 (`/api/analyze` 400-vs-500 fix), #48 (frontend: clear backend-unreachable error + real screenshots) all merged
- All Session 21 fixes merged: PR #49 (CORS), #51 (ImportError detail), #52 (`Dockerfile` `[vertex]` extra + docs — recovered after #49/#51 both dropped commits pushed post-merge, see Session 21 item 5), #53 (frontend live-deploy docs). `ok: true` summary path verified live for real
- Phase 0/3/7/8/9/13/15/16: 🟢. Phase 11: 🟢 (see Session 20) — first genuinely successful live AI fix-loop run, 89.87%/71/79. Phase 17 B1/B2: 🟢 (Terraform-managed WIF)
- Phase 14: 🟡 — PR #43 closed gaps 4/5/6, PR #44 added visual design, PR #48 added a clear backend-unreachable error + real production screenshots, PR #50 shows the backend's error `detail`. `NEXT_PUBLIC_REPOGUARD_API_BASE` now points at the real Cloud Run URL (Vercel, type "Config" not "Secret" since it's not sensitive), verified end-to-end including CORS (Session 21-front). Remaining: gap 3 (Autofix) is built (Session 22), and its live run is waiting on `REPOGUARD_FIX_TOKEN` being attached on Cloud Run (`docs/DEPLOY.md` §5). The summary's `ok=true` path is verified live (Session 21). Analyze *with* mutation against Cloud Run's request timeout is unchecked
- Phase 17 A1-A3 (DB store) and C1-C2 (charts) still 🔴, but `docs/DATA_PLATFORM.md` §13 now has a corrected, step-by-step Block A build plan (Session 20) — build from that, not the doc's original sketch
- Phase 18 (swarm) still 🔴, `docs/MULTI_AGENT_SWARM.md` §14 now has a corrected S0–S8 plan + 15 risks (Session 20) — Phase 11's merge (PR #45) clears its §14 R1 blocker; demo-repo's 71/79 ceiling still means H2 can only tie there (§14 R2)
- IBM Bob is retired. `.bob/` stays on disk as inert legacy (`.bob/DEPRECATED.md`); `repoguard_engine/watson_agent/` is the live replacement.
- GCP Cloud Run: identity is Terraform-managed and a real deploy has succeeded. `GCP_PROJECT_ID`'s raw value in GitHub Settings still has the leading space (cosmetic — `cd.yml` auto-trims it every run; clean it up next time you're in Settings)
- **Done, human-run:** `roles/aiplatform.user` granted to the Cloud Run runtime SA (`993240087609-compute@developer.gserviceaccount.com`) — confirmed in the real IAM policy. Was blocked for an agent session (Claude Code's auto-mode classifier blocks IAM permission grants regardless of scope), so the user ran `gcloud projects add-iam-policy-binding ...` directly
- Open, not yet decided: repo rename; tightening `repoguard-deployer`'s 3 project-wide IAM roles (`infra/terraform/README.md`); whether the new `aiplatform.user` grant above should also move into `infra/terraform/` for consistency (suggested by the frontend session); the 6 Phase 17 decisions (now listed with recommendations in `docs/DATA_PLATFORM.md` §13's table) and 15 Phase 18 risks (`docs/MULTI_AGENT_SWARM.md` §14)
- Unexplained, found mid-session: an auto-generated `bobalytics` usage-stats update to `README.md` (badge reorder + a new dated impact row) sitting uncommitted in the working tree, origin unknown — left alone, not folded into any PR

---

## How to resume

1. Read `PENDING.md` for the task list (Phase 11 is now 🟢 — read its "3 attempts, 3 bugs" narrative before touching `watson_agent/` again, it explains real, non-obvious API constraints).
2. Run `python scripts/verify.py phase0`, `phase3`, `phase7`, `phase15`, `phase16`, `multicloud`, `phase14fix`, `phase14ui` (needs `npm ci` in `web-next/`) to confirm baseline holds. (`ci.yml` doesn't run `phase14fix` yet; it's credential-free, so it could.)
3. Frontend punch-list items 1-4 are all done and verified live (Session 21). Autofix (`POST /api/fix`, Phase 14 gap 3) is built (Session 22); what's left is the human token step plus a first live run. When pushing follow-up commits to a branch mid-session, confirm with `git log origin/main..<branch>` that nothing merged out from under you first (Session 21 item 5 — happened 3 times).
4. Build Phase 17/18 from `docs/DATA_PLATFORM.md` §13 / `docs/MULTI_AGENT_SWARM.md` §14, not their original sketches.
5. Autofix: attach `REPOGUARD_FIX_TOKEN` (`docs/DEPLOY.md` §5), then run it from the Vercel demo against `demo-repo` and record the measured before/after. If you change a Vercel env var, Redeploy the **newest `main`** deployment, never an older row (`docs/ARCHITECTURE-front.md`, Session 21-front item 5).
6. If tightening `repoguard-deployer`'s IAM roles, or moving the new `aiplatform.user` grant into Terraform: read `infra/terraform/README.md`'s "Known gap" section first — real permissions change against a live project, own PR.
7. The repo-rename decision is open and low-urgency — decide whenever, it's cosmetic.
