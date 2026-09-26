# Setting up Google Vertex AI (not built yet)

**`ai_providers/vertex.py` doesn't exist yet.** `REPOGUARD_AI_PROVIDER=vertex`
and `--provider vertex` are already wired into `ai_providers/get_provider()`,
`repoguard fix`, and `repoguard analyze --summarize`, but selecting `vertex`
today raises `AIProviderError("Unknown REPOGUARD_AI_PROVIDER: 'vertex' ...")`
until this is implemented — see `docs/MULTICLOUD_AI.md`'s Stage B and
`PENDING.md` Phase 16.

This file will become the Vertex-AI sibling of `docs/WATSONX_SETUP.md` once
that lands: a GCP project + service account, `pip install -e ".[vertex]"`,
the real env vars (`GOOGLE_APPLICATION_CREDENTIALS`, `VERTEX_PROJECT_ID`,
`VERTEX_LOCATION`, `VERTEX_MODEL_ID`), a "try it" section, and a "what was
and wasn't verified" section populated from a real live SDK/credentials
check — not written speculatively ahead of that verification, per
`AGENTS.md` Section 4's rigor rule.
