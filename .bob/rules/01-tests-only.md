# Rule 01 — Tests Only

When operating in fix mode, **only create or modify files inside a `tests/` directory**.

- Do NOT modify source files (`*.py` outside `tests/`) unless explicitly instructed.
- Do NOT refactor production code to make it easier to test — write tests that test it as-is.
- Do NOT add test helpers or fixtures outside `tests/conftest.py`.
- If a source file needs to change to be testable, stop and report the blocker instead of making the change.

This rule applies to the Fixer sub-agent and any mode that writes test files.
