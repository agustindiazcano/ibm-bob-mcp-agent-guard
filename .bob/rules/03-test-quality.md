# Rule 03 — Test Quality Standards

Every test written by Bob must meet these standards:

## Structure
- One `assert` per logical check — avoid multi-assert tests that hide which assertion failed.
- Use descriptive test function names: `test_<function>_<scenario>_<expected_outcome>`.
- Group related tests in a class only when shared fixtures justify it.

## Coverage
- Each test must exercise a specific branch, not just the happy path.
- Edge cases required: empty input, boundary values, error/exception paths.
- Do not write tests that only assert `True` or `is not None` without meaningful checks.

## Independence
- Tests must not depend on execution order.
- Tests must not share mutable state unless via explicit pytest fixtures.
- No `time.sleep()` in tests — use mocks or `freezegun` for time-dependent code.

## Mutation Resistance
- Assertions must be specific enough to catch off-by-one errors and sign flips.
- Prefer `assert result == expected` over `assert result` for numeric results.
- Cover both the true and false branches of conditionals.

## Anti-patterns (prohibited)
- `assert True` or `assert 1 == 1` (trivial tests)
- Tests with no assertions
- Catching all exceptions with bare `except:` in tests
- Hardcoded sleep / wall-clock waits
