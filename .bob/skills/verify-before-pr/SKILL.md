---
name: verify-before-pr
description: Use before opening a PR, marking a phase done, or merging any branch — runs scripts/verify.py for the relevant phase check, validates the output is PASS, and ensures measured numbers in docs match. Activate when the user says "open PR", "ready to merge", "phase done", or "create pull request".
---

# Verify Before PR

Run this checklist every time before opening a PR or marking a phase complete.
Never skip it — a failing verify.py must block the PR, not just warn.

## Step 1 — Identify the phase check

Determine which phase this branch corresponds to by looking at:
1. The branch name (e.g. `feat/03-mutation` → phase 3)
2. The files changed in the branch (`git diff main --name-only`)
3. The `PENDING.md` phase table

## Step 2 — Run verify.py

```bash
python3 scripts/verify.py <phase-check>
```

Example phase checks:
- `python3 scripts/verify.py phase-0`  — skeleton and config
- `python3 scripts/verify.py phase-3`  — mutation engine
- `python3 scripts/verify.py phase-7`  — MCP server
- `python3 scripts/verify.py demo`     — full demo-repo baseline

Use the `execute_command` tool to run it. Capture the **full stdout output** — this is what goes in the PR description.

## Step 3 — Gate on the result

- If the output contains **PASS** → continue to Step 4.
- If the output contains **FAIL** → **stop**. Do not open the PR.
  - Report the failing check to the user.
  - Ask what should be fixed before retrying.
  - Do not proceed until verify.py exits 0 with PASS.

## Step 4 — Check numbers in docs (if any changed)

If the branch changes a measured number (coverage %, mutation score, endpoint count, visual diff threshold):

1. Find every place that number appears in `README.md`, `docs/ARCHITECTURE.md`, and `docs/DEMO.md`.
2. Compare against the verify.py output.
3. If any doc number is stale, update it in this same branch before opening the PR.
4. Do not open a PR where a number in docs differs from what verify.py just measured.

## Step 5 — Draft the PR description

Use this template:

```
## What this PR does
<one paragraph>

## verify.py output
```
<paste full output here>
```

## Docs updated
- [ ] README.md — <which numbers, or "no measured numbers changed">
- [ ] docs/ARCHITECTURE.md — <which numbers, or "n/a">
- [ ] docs/DEMO.md — <which numbers, or "n/a">

## Checklist
- [ ] verify.py exits 0 with PASS
- [ ] No source files modified (Fixer/Test Writer PRs only)
- [ ] PENDING.md phase table updated to 🟢 for completed deliverables
- [ ] LASTCONTEXT.md updated
```

## Step 6 — Open the PR

Use the GitHub MCP tool or `gh pr create` with the description from Step 5.
Only open the PR when all checklist items above are checked.

## What this skill does NOT do

- It does not run verify.py if `scripts/verify.py` does not exist yet — instead, report
  "scripts/verify.py is missing — see PENDING.md standalone tasks" and stop.
- It does not bypass the FAIL gate under any circumstances.
- It does not update numbers without running verify.py first (Rule 02: measure, don't guess).
