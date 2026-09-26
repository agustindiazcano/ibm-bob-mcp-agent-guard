# This directory is retired

IBM Bob is no longer the agent platform for this project. Everything in
`.bob/` (`custom_modes.yaml`, `mcp.json`, `settings.json`, `hooks/*.mjs`,
`rules/`, `skills/`) is left here as-is for historical reference — none of it
runs anything anymore, and nothing in `repoguard_engine/` depends on it.

The live replacement is `repoguard_engine/watson_agent/` (a watsonx.ai
tool-calling orchestrator, invoked via `repoguard fix`). The substance of
`.bob/rules/*.md` and `.bob/skills/*/SKILL.md` was carried forward into
`repoguard_engine/watson_agent/prompts.py`; the "tests/ only" rule that used
to need `hooks/safety-guard.mjs` to enforce is now a hard property of
`watson_agent/tools.py`'s `write_test_file` function instead of an external
hook.

`BOBREADME.md` (repo root) is the same kind of leftover — generic IBM Bob
platform documentation, not project instructions, safe to ignore.

See `AGENTS.md` §2 and §5, and `docs/ARCHITECTURE.md`, for the current
architecture.
