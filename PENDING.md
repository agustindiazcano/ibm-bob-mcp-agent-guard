# Pending Tasks

> Ordered list of outstanding work. Update this file whenever a task is started, completed, or added.  
> Format: `- [ ]` pending · `- [-]` in progress · `- [x]` done.

---

## In progress

_(none)_

---

## Up next

- [ ] **Create `scripts/verify.py`** — phase-check script referenced in `AGENTS.md § 11`. Must accept a phase name argument (e.g. `python3 scripts/verify.py feat/03-mutation`) and output PASS/FAIL with the measured numbers. Output should be pasteable into a PR description.
- [ ] **Add `LASTCONTEXT.md` and `PENDING.md` to the project tree** in `README.md` and `AGENTS.md` (they were created after the last tree snapshot).
- [ ] **Write engine tests** — `repoguard_engine/` has no `tests/` directory of its own. Run `repoguard gate .` and fix gaps to reach ≥ 80% coverage on the engine itself.
- [ ] **Populate `bob-evidence/`** — export at least one real Bob task session report to `bob-evidence/01-initial-build.md` following the convention in `AGENTS.md § 11`.
- [ ] **Verify demo-repo baseline numbers** — run `repoguard analyze ./demo-repo` and confirm the numbers match the documented values (74.5% coverage, 23.6% mutation score, 6/8 endpoints untested).
- [ ] **Add `.gitattributes`** — normalize line endings (CRLF warnings on every commit suggest this is missing).

---

## Backlog

- [ ] **Flesh out `docs/BUILD_WITH_BOB.md`** — currently a stub; add phase-by-phase prompts as described in the file header.
- [ ] **Populate `docs/img/`** — `README.md` references `docs/img/results-en-dark.png` and `docs/img/results-en-light.png`; these don't exist yet.
- [ ] **`repoguard fix` implementation** — currently prints a "use Bob" message; wire it to Bob Shell (`bob run --mode orchestrator`).
- [ ] **CI workflow** — add `.github/workflows/gate.yml` using the snippet from `RUNBOOK.md § 7`.
- [ ] **Playwright install in CI** — document or automate `playwright install chromium` for visual checks in CI.

---

## Done

- [x] Initialize git repo and connect to GitHub remote
- [x] Create `RUNBOOK.md`
- [x] Expand project tree in `README.md`
- [x] Expand project tree in `AGENTS.md`
- [x] Update `AGENTS.md § 11` with branch-per-phase and `verify.py` gate rules
- [x] Add session-start instruction at top of `AGENTS.md`
- [x] Create `LASTCONTEXT.md` and `PENDING.md`
