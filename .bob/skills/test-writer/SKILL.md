---
name: test-writer
description: Use when writing tests that target specific surviving mutants — walks through reading the mutant report, selecting the highest-risk survivors, and writing mutation-resistant assertions that kill them. Activate when the Test Writer subagent starts work on a file.
---

# Test Writer — Killing Surviving Mutants

Follow these steps exactly. Do not skip steps or reorder them.

## Step 1 — Read the gap report (never guess)

Call `tool_find_gaps` (or read `repoguard-out/gaps.json` in the target repo) to get the list of
uncovered functions per file. Then call `tool_run_mutation` with `detail=True` to get the list of
surviving mutant IDs and their locations.

Do NOT propose any test until you have both artefacts in context.

## Step 2 — Triage survivors by risk

Sort surviving mutants by the function's risk score (from `repoguard-out/risk.json` if available,
else by covered-lines ratio). Work the highest-risk file first. Within a file work mutants in
source-line order.

## Step 3 — Read the source before writing the test

For each mutant you plan to kill:
1. Read the exact lines around the mutation site (use `read_file` with a `range`).
2. Understand what the original operator does and what the mutant changes it to.
3. Identify the input that would produce a different output for the mutant vs the original.

## Step 4 — Write the killing test

Rules that apply to every test you write:

- File: `tests/test_<module>.py` (create if absent, append if exists).
- Name: `test_<function>_<scenario>_<expected_outcome>`.
- One logical assertion per test — prefer `assert result == expected` over `assert result`.
- The assertion value must be the exact correct answer, not a rounded or approximate value.
- Cover the true AND false branch of every conditional you touch.
- For arithmetic mutants: assert the precise numeric result (not just that it is positive).
- For comparison mutants: write a test at the boundary (n-1, n, n+1) to catch off-by-one flips.
- For boolean mutants: assert both the `True` and `False` outcomes explicitly.
- For `return None` mutants: assert `result is not None` AND assert the correct type/value.
- For `remove raise` mutants: use `pytest.raises(ExceptionType)` with the exact message if possible.

## Step 5 — Verify the test kills the mutant (mental model check)

Before writing, trace through the mutated code with your test input mentally:
- Would the original code pass the test? (must be YES)
- Would the mutated code fail the test? (must be YES)

If both answers are YES, write the test. If not, rethink the assertion or the input values.

## Step 6 — Do NOT touch source files

You may only create or modify files under `tests/`. If the test cannot be written without changing
source code, add a comment `# NOTE: requires source change to test` and skip that mutant. Report
it as a blocker in your summary.

## Step 7 — Report what you wrote

After finishing a file, output a compact table:

| Mutant ID | Function | Operator | Test name | Killed? |
|---|---|---|---|---|
| M-12 | apply_discount | ComparisonOp | test_apply_discount_boundary_10pct | yes |

List any mutants you could not kill and why (equivalent mutant, requires source change, etc.).
