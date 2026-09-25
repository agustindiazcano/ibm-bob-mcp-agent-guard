# Rule 04 — Token Budget

Keep context lean so Bob can sustain a long fix cycle without compaction cutting off mid-run.

## What to keep out of context

- Do NOT read `repoguard-out/*.json` files unless the current task explicitly needs the raw data.
- Do NOT read images (`docs/img/`, `bob-evidence/` screenshots) unless doing visual comparison.
- Do NOT read `docs/expected-after-tests/` unless the current task is verifying "after" numbers.
- Do NOT re-read a file you just wrote in the same session.

## How to read files

- Read only the section you need: use `range` on `read_file` when the target is large.
- Prefer `grep` over `read_file` for locating symbols or patterns.
- After a `repoguard analyze` run, read only the summary table — not the full JSON output.

## Subagent discipline

- Spawn at most **3 subagents per round**.
- Pass each subagent only the data it needs: its target file and its gap/mutant data.
- Do NOT pass the full conversation history to a subagent — use `fork_context: false`.

## Replies

- Reply with tables and lists, not prose re-stating tool output.
- Do not repeat information that is already in the tool result or a previous message.
- Keep evidence exports (bob-evidence/) to the final assistant message of a task, not mid-session.
