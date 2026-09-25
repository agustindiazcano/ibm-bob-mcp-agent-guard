# Claude review — Phase 0 verification and Phase 3/7 plan (`feat/03-mutation`)

Independent review done outside the Bob swarm, based on actually running the
commands rather than trusting session logs. Recorded here so it survives
context resets and both agents (and the human) are working from the same
findings.

## Phase 0 re-verification (PR #2, merged to `main`)

Confirmed genuine, by reinstalling `repoguard` in a clean venv and running it:

- `python scripts/verify.py phase0` → real PASS in an isolated venv.
- `build-backend`, `requires-python`, `.gitignore`/`.bobignore`, and the
  `playwright`/`pillow` dependency additions all check out.

`scripts/verify.py`'s `run()` calls `subprocess.run` with no `timeout=`,
which violates AGENTS.md §6 ("blocking subprocess calls always have a
timeout"). Small, but the gate script shouldn't break the rule it enforces.

## Findings that motivated the `feat/03-mutation` branch

1. **`run_mutation()` shells out to `mutmut`.** AGENTS.md §2/§3 is explicit:
   "own mutation engine (stdlib `ast`), no mutmut/Stryker." Confirmed by
   running `repoguard analyze demo-repo --mutation --endpoints`, which
   crashed with `FileNotFoundError: mutmut`. This is the product's core
   differentiator built the wrong way — not a missing dependency, a wrong
   implementation.
2. **`repoguard-out/*.json` is never written.** AGENTS.md §4 calls this
   folder "the contract between agents" since subagents don't share memory.
   Ran the full pipeline against demo-repo; no `repoguard-out/` directory
   was created. Nothing in `core.py`/`pipeline.py` writes it today. Phase 11
   (real Bob swarm run) depends on this contract existing.
3. **`compute_risk()` doesn't implement its documented formula.** PENDING.md
   marks `risk_score()` 🟢 with "complexity × git churn × (1 − detection
   rate)"; the actual code (`core.py`) is just `uncovered_lines /
   total_lines`. Deferred — Phase 4, not in scope for this branch — but
   noted so the 🟢 isn't trusted at face value later.
4. **Baseline numbers in AGENTS.md §7 don't match reality.** Ran the actual
   demo-repo suite: 5 tests pass, not the documented 9.
   `repoguard analyze .` (no flags) gave 65.1% coverage, not 74.5%.

## Review of Bob's `feat/03-mutation` plan (3 sub-tasks, 1 branch)

Plan is correctly scoped at the root problem. Answers to the two questions
Bob raised before handoff:

**Q1 — should the new engine's mutation score match the old `23.6%, 17/72`?**
No. That number came from `mutmut`, a different engine with different
mutant generation. Forcing the new engine to match it would be estimating a
result instead of measuring one, which AGENTS.md forbids outright. Measure
fresh with the new engine and overwrite the table with the real number,
whatever it is.

**Q2 — should `repoguard fix` (Phase 9) be wired up in this same branch?**
No. It depends on Phases 4–6, not Phase 3; its Bob Shell invocation is
already flagged in AGENTS.md §9 as unverified; and bundling an unverified
integration into a full engine rewrite makes it harder to isolate a
regression if one appears. Give it its own branch later, per the
one-branch-per-phase rule in §11.

**Two additions folded into the same branch, since Sub-Task 1/3 are already
touching this code:**

- Sub-Task 1 (or a Sub-Task 4): have `run_mutation()` — and ideally the rest
  of the pipeline — write its result to `repoguard-out/mutation.json` (and
  equivalents for coverage/gaps/risk if not already happening). Closes
  finding #2 above while the mutation code is already being rewritten.
- Sub-Task 3: before re-measuring, reconcile the demo-repo test count
  (AGENTS.md §7 says 9, actual is 5) — independent of the mutation engine,
  but the same PR that rewrites the verification table is the right place
  to fix it, rather than leaving the table stale in two ways at once.
