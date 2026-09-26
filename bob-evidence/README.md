# Bob usage evidence

Each file is a task session report exported from Bob. Name it `NN-stage.md`, save it here, and check off this table as each one lands.

| # | Stage | What Bob did | File |
|---|---|---|---|
| 01 | AI-assisted development setup | Configured `.bob/hooks/` (`safety_guard`, `evidence_export`) and `.bob/skills/`; confirmed what ended up as a hook vs. a rule | `01-ai-dev-setup.md` |
| 02 | Project setup | Phases 0–1: skeleton, `pyproject.toml`, `AGENTS.md`, `demo-repo/` fixture | `02-project-setup.md` |
| 03 | Core engine | Phase 2–3: `run_tests`, `coverage_report`, `scan_repo`, the AST mutation engine | `03-core-engine.md` |
| 04 | MCP server | Phase 7: `mcp_server.py` and `.bob/mcp.json` | `04-mcp-server.md` |
| 05 | Bob modes | Phase 8: orchestrator + subagent modes, rules, skills | `05-bob-modes.md` |
| 06 | Documentation generation | README, `docs/ARCHITECTURE.md`, `docs/DEMO.md`, the AI-assisted development framework section | `06-documentation.md` |
| 07 | Diagnosis | 🛡️ TestMind mode: coverage vs. mutation score on `demo-repo` (baseline) | `07-diagnosis.md` |
| 08 | Parallel subagents | Test Writer subagents running in parallel, one per file (screenshot of the subagent panel) | `08-subagents.md` + `.png` |
| 09 | Verification | Fixer loop + mutation score "after" | `09-verification.md` |
| 10 | Audit | Critic subagent reviewing the new tests | `10-critic.md` |
| 11 | Close | Dashboard + PR created by the Publisher subagent | `11-pr.md` + link |

## Notes
- A row only counts once its file exists here with the real exported report — a written summary is not evidence.
- If `evidence_export` (the after-task hook) is working, rows 07–11 should populate automatically as the 🛡️ TestMind mode runs; rows 01–06 are exported by hand from each setup/build session.
- Keep the numbering sequential even if a stage gets re-run (e.g. a second diagnosis run is `12-diagnosis-rerun.md`, not a second `07`).

# Bob IDE Usage Dashboard (IBM)

**Team:** Team Argentina
**Member:** Agustin
**Repository:** agustindiazcano/ibm-bob-mcp-agent-guard

---

## 1. Hackathon Ranking Position

| Metric | Value | Ranking |
|---|---|---|
| Bob Commits | 12 | 1st of 6 |
| Bob Lines | 820 | 14th of 14 |
| Bob Factor | 16.0% | 21st of 21 |

---

## 2. Spending

| Team Name | Spending limit | Usage | Remaining |
|---|---|---|---|
| Team Argentina | 40 Bobcoins | 40 Bobcoins | 0 Bobcoins |

---

## 3. Bob's Repository Impact

| Repository | Bob Lines | User Lines | Total Lines | Bob factor | Bob commits |
|---|---|---|---|---|---|
| agustindiazcano/ibm-bob-mcp-agent-guard | 820 | 4,314 | 5,134 | 16.0% | 12 |

---

## 4. Modes (42 tasks total)

| Mode | Tasks | % |
|---|---|---|
| agent | 37 | 88.1% |
| plan | 5 | 11.9% |

---

## 5. Bob's Language Contribution (1.2k LOC total)

| Language | LOC | % |
|---|---|---|
| md | 1.1k | 97.8% |
| unknown | 25 | 2.2% |