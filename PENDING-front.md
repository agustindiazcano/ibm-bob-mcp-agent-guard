# PENDING-front.md — Phase 14: Next.js dashboard on Vercel

**Satellite tracker — kept separate from `PENDING.md` on purpose, so this
branch (`feat/14-nextjs-dashboard-arch`) doesn't fight the backend branch
over the same Phase 14 section. Fold this back into `PENDING.md`'s own
Phase 14 entry at merge time.**

**Priority: 2 · Depends on: 9, 10** (frontend only — no engine changes)

Decision: no Terraform, no new GCP infrastructure for this piece.
`docs/DEPLOY.md` / Cloud Run (Phase 13) is left as-is for the existing
FastAPI service; this phase adds a separate, richer frontend deployed to
Vercel that consumes the existing `/api/analyze` and `/api/stream`
endpoints — see `docs/ARCHITECTURE-front.md` for the full route/component
breakdown and data contract.

**Multicloud note:** the AI layer is moving to a provider-agnostic
`ChatProvider` abstraction — watsonx.ai + Google Vertex AI, not watsonx.ai
alone — design in `docs/MULTICLOUD_AI.md`, not built yet. `AnalyzeResponse`
and the SSE stream are pure measurement and don't change either way; gaps
3, 4 and 6 below do.

## Backend gaps this phase depends on

| # | Gap | Blocks | Fix belongs to |
|---|---|---|---|
| 1 | ~~`web/server.py` has no `CORSMiddleware`~~ — fixed, `REPOGUARD_CORS_ORIGINS` env var (default `localhost:3000`) | any browser call from a Vercel origin | done |
| 2 | — | (Gate needs no new endpoint — `/api/analyze?gate_threshold=N` already returns `passed_gate`) | — |
| 3 | No `POST /api/fix` — the fix loop is CLI-only | Autofix button | ship v1 with it disabled; revisit once the fix loop *and* `docs/MULTICLOUD_AI.md`'s `ChatProvider` are both stable, so the endpoint isn't built twice |
| 4 | No summary endpoint (`generate_summary` is MCP/CLI-only) | `SummaryPanel` | backend (`web/server.py`), ideally after `ai_providers.get_provider()` lands so it returns `provider` from day one |
| 5 | `/api/stream`'s gate check hardcodes 80% and ignores threshold | live-progress gate readout | backend (`web/server.py`) |
| 6 | Nothing surfaces which AI provider ran (only watsonx.ai has ever existed) | `SummaryPanel` labeling, future Autofix result view | backend, once `ChatProvider` exists — add a `provider` field to gaps 3/4's future responses |

## Deliverables

| Deliverable | Description | Status |
|---|---|---|
| Next.js app scaffold | New `web-next/`, calling the existing FastAPI backend, not replacing it | 🟢 |
| `RepoForm` + `ActionBar` | Repo path input, mutation/endpoints/threshold options, Analyze + Gate buttons (Autofix disabled — gap 3) | 🟢 |
| `StreamLog` | Live progress from `/api/stream`, rendering only the event types it actually emits (coverage/gaps/risk) | 🟢 |
| `StatCards` + `GapsList` + `RiskTable` | Coverage, mutation score, gaps, risk ranking — sourced verbatim from `AnalyzeResponse`, no new numbers invented | 🟢 |
| `SummaryPanel` | AI prose, labeled advisory + which provider generated it — blocked on backend gaps 4 and 6 | 🔴 |
| Vercel deploy | Connect repo/subfolder to Vercel; no IaC, config lives in `vercel.json` / project settings; `NEXT_PUBLIC_REPOGUARD_API_BASE` env var per environment | 🔴 |
| Docs | Fold this file and `docs/ARCHITECTURE-front.md` back into `PENDING.md`/`docs/ARCHITECTURE.md`, update `README.md`, once built | 🔴 |

**Verified so far:** `npm run lint` and `npm run build` both pass; `next dev`
was run directly and served the real page (200, title "TestMind AI"). Not
yet verified: an end-to-end fetch against a real running `repoguard serve`
backend — blocked on gap 1 (`CORSMiddleware`), which lives on a separate,
not-yet-merged branch (`fix/web-cors`).
