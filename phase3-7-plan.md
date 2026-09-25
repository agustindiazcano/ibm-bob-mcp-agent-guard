# Plan: Phase 3 (Mutation Determinism) + Phase 7 (MCP Compact Responses)

## Overview

Four sub-tasks, one branch (`feat/03-mutation`). All decisions confirmed by user + Claude independent review (`docs/claude-review-phase3-mutation.md`).

**Key decisions recorded:**
- Q1: Do NOT try to match the old `23.6%, 17/72` mutmut numbers. Measure fresh with the new AST engine and write whatever the real numbers are into `AGENTS.md §7`.
- Q2: `repoguard fix` (Phase 9) stays out of this branch — it depends on Phases 4–6 and its Bob Shell invocation is unverified. Own branch later.
- New finding from Claude review: `repoguard-out/` is never written by `core.py` / `pipeline.py` despite being "the contract between agents" per `AGENTS.md §4`. Fix it now while mutation code is being rewritten.
- New finding from Claude review: `AGENTS.md §7` says "9 tests pass" but actual demo-repo suite has 5. Reconcile in this same PR.
- `scripts/verify.py` subprocess calls have no `timeout=` — fix while touching that file.

Scope boundary: `repoguard_engine/core.py`, `repoguard_engine/pipeline.py`, `repoguard_engine/mcp_server.py`, `scripts/verify.py`, `AGENTS.md`, `PENDING.md`, `LASTCONTEXT.md`. No demo-repo shop/web source files. No test files outside `tests/` of this repo.

---

## Sub-Task 1 — Own AST mutation engine + `repoguard-out/` writes

### Intent
Replace the two `subprocess.run(["mutmut", ...])` calls in `run_mutation()` with a self-contained AST mutation loop that:
- Parses each `.py` source file with `ast`
- Applies mutation operators one at a time via `ast.NodeTransformer` subclasses
- Writes the mutated source to a `tempfile.mkdtemp()` copy of the repo
- Runs `pytest -q --tb=no` on the temp copy with `PYTHONDONTWRITEBYTECODE=1` in env
- Records killed vs survived, populates `surviving_mutant_ids`
- Cleans up the temp copy after each mutant (per `AGENTS.md §6`)

Also: have `run_mutation()`, `measure_coverage()`, `find_coverage_gaps()`, and `compute_risk()` each write their result to `repoguard-out/<name>.json` inside the target repo. This closes the "contract between agents" gap identified in the Claude review.

### Mutation operators required (per `AGENTS.md §3` and `PENDING.md Phase 3`)
| Operator | What it changes |
|---|---|
| comparison | `==` → `!=`, `<` → `>=`, `>` → `<=`, `<=` → `>`, `>=` → `<`, `!=` → `==` |
| arithmetic | `+` → `-`, `-` → `+`, `*` → `/`, `/` → `*` |
| boolean | `and` → `or`, `or` → `and`, `not x` → `x` |
| constants | `True` → `False`, `False` → `True`, numeric literals: n → n+1 |
| return None | `return <expr>` → `return None` (skip if expr is already None) |
| remove raise | `raise ...` → `pass` |

### Expected Outcomes
- `run_mutation()` no longer calls `mutmut`; `mutmut` removed from `pyproject.toml` if listed
- Running `run_mutation()` twice on `demo-repo` produces identical output
- `surviving_mutant_ids` is populated
- `PYTHONDONTWRITEBYTECODE=1` is in env of every pytest subprocess
- `repoguard-out/coverage.json`, `repoguard-out/gaps.json`, `repoguard-out/mutation.json`, `repoguard-out/risk.json` are written to the target repo after each respective function call
- `repoguard analyze ./demo-repo` completes without crashing

### Todo List
- [ ] Check `pyproject.toml` for `mutmut` dependency and remove it if present
- [ ] Write `_generate_mutants(source_path: Path) -> list[Mutant]` using `ast.NodeTransformer` for each operator class; `Mutant` is a simple dataclass: `index: int`, `description: str`, `mutated_source: str`
- [ ] Write `_run_mutant(repo_path, file_rel, mutated_source, tests_dir) -> bool` — copies repo to tempdir, writes mutant, runs pytest with `PYTHONDONTWRITEBYTECODE=1`, returns True if killed, always deletes tempdir
- [ ] Replace `run_mutation()` body with the new loop; populate `surviving_mutant_ids`
- [ ] Add `repoguard-out/` write logic to: `measure_coverage()`, `find_coverage_gaps()`, `run_mutation()`, `compute_risk()` — write JSON to `<repo_path>/repoguard-out/<name>.json`; create the dir if absent
- [ ] Add `timeout=` to all `subprocess.run()` calls in `core.py` (per `AGENTS.md §6`)

### Relevant Context
- `repoguard_engine/core.py` lines 78–123 — current `run_mutation()` to replace
- `repoguard_engine/core.py` `MutationResult` dataclass — `surviving_mutant_ids: list[int]` field exists but is never populated
- `AGENTS.md §3` — "stdlib ast (own mutation engine, no mutmut/Stryker)"
- `AGENTS.md §4` — "`repoguard-out/` is the contract between agents"
- `AGENTS.md §6` — "Mutation work copies are deleted after the run"; "blocking subprocess calls always have a timeout"
- `docs/claude-review-phase3-mutation.md` — confirms mutmut crash and missing repoguard-out/

### Status
[ ] pending

---

## Sub-Task 2 — MCP compact responses (`detail` parameter)

### Intent
Every MCP tool currently returns its full payload on every call. Per `AGENTS.md §4` ("MCP tools return summaries by default and full data only with `detail=True`"), add a `detail: bool = False` parameter to all 8 tools.

### Compact response design (per tool)
| Tool | Compact (detail=False) | Full (detail=True) |
|---|---|---|
| `tool_measure_coverage` | `{percent, covered_lines, total_lines}` | + `missing_lines_by_file` |
| `tool_find_gaps` | `{coverage_percent, uncovered_file_count, uncovered_files}` | + `missing_lines_by_file` |
| `tool_run_mutation` | `{score, killed, survived, total}` | + `surviving_mutant_ids` |
| `tool_find_untested_endpoints` | `{untested_count, untested_paths}` | full list with file/function/method |
| `tool_smoke_test_endpoints` | `{ok_count, fail_count, failures}` | full map of all endpoints |
| `tool_full_pipeline` | `{coverage_percent, mutation_score, gap_count, passed_gate}` | full dashboard dict |
| `tool_capture_screenshot` | `{ok, path}` | + width, height, error |
| `tool_check_accessibility` | `{violation_count, violations}` | + passes, incomplete |

### Expected Outcomes
- All 8 tools accept `detail: bool = False`
- Default call (no `detail`) returns only the compact fields
- `detail=True` returns full payload (same as today)
- No stdout writes in `mcp_server.py` (architecture rule)

### Todo List
- [ ] Read `repoguard_engine/mcp_server.py` in full
- [ ] Add `detail: bool = False` param and compact/full branches to each of the 8 tools
- [ ] Verify no `print()` calls exist in `mcp_server.py`

### Relevant Context
- `repoguard_engine/mcp_server.py` — all 8 `@mcp_app.tool()` functions
- `AGENTS.md §4` — compact MCP responses rule + no stdout rule

### Status
[ ] pending

---

## Sub-Task 3 — Reconcile demo-repo test count, measure, update docs + `scripts/verify.py`

### Intent
Before re-measuring with the new engine, reconcile the known discrepancy: `AGENTS.md §7` says "9 tests pass" but `docs/claude-review-phase3-mutation.md` confirms only 5 actually run. Either the doc is wrong or the test suite is incomplete. Determine which, fix the doc or add missing tests (only in `demo-repo/tests/`, never in `shop/`), then do a full fresh measurement and overwrite the `AGENTS.md §7` table with real numbers.

Also: add `timeout=` to subprocess calls in `scripts/verify.py` (same rule violation found in the Claude review).

### Expected Outcomes
- `demo-repo/` suite passes (count reconciled with what `AGENTS.md §7` says)
- `repoguard analyze ./demo-repo` completes without crashing
- `AGENTS.md §7` verification table updated with real, measured numbers from the new AST engine
- `scripts/verify.py phase3` → PASS
- `scripts/verify.py phase7` → PASS (or added if missing)
- All subprocess calls in `scripts/verify.py` have `timeout=`

### Todo List
- [ ] Run `cd demo-repo && python -m pytest -q` and record actual test count
- [ ] Check whether the gap is a doc error (just update `AGENTS.md §7`) or missing tests (add them to `demo-repo/tests/`)
- [ ] Run `repoguard analyze ./demo-repo` with the new AST engine and capture all numbers
- [ ] Update `AGENTS.md §7` table with the real measured numbers
- [ ] Add `phase3` and `phase7` checks to `scripts/verify.py` (or update if partially there); add `timeout=` to all subprocess calls in that file
- [ ] Mark Phase 3 "Determinism" 🔴 → 🟢 and Phase 7 "Compact responses" 🔴 → 🟢 in `PENDING.md`
- [ ] Update `LASTCONTEXT.md` with a session summary entry
- [ ] Commit all changes on `feat/03-mutation`

### Relevant Context
- `docs/claude-review-phase3-mutation.md` finding #4 — 5 tests run, not 9
- `AGENTS.md §7` — verification table (coverage 74.5%, mutation 23.6% are now known-wrong; replace with measured values)
- `AGENTS.md §8` — "Ask before doing: changing documented numbers without a real measurement behind them"
- `scripts/verify.py` — add timeout to subprocess calls; add phase3/phase7 checks

### Status
[ ] pending

---

## Out of scope (explicitly deferred)
- `repoguard fix` (Phase 9) — unverified Bob Shell invocation; own branch later
- `compute_risk()` formula fix — PENDING.md marks it 🟢 but code doesn't match documented formula; Phase 4 work
- `feat/07-mcp-server` branch for remaining Phase 7 items (only "compact responses" is in scope here)
