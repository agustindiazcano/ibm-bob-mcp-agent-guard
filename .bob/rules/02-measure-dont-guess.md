# Rule 02 — Measure, Don't Guess

**Always run a measurement tool before proposing or writing any fix.**

- Run `repoguard analyze` (or the `measure_coverage` MCP tool) on the target repo first.
- Base all decisions on the actual output: coverage %, uncovered line numbers, missing function names.
- Do NOT assume which tests are missing — read the gap report.
- Do NOT re-run measurement mid-fix unless a threshold check is required.
- After fixes are applied, run measurement again to confirm improvement.

Guessing which tests to write without measuring first is a disallowed pattern.
