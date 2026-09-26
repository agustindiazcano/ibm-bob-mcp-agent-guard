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
| 4 | ~~No summary endpoint~~ — fixed, `POST /api/summary` (body: `/api/analyze`'s dashboard; returns `{ok, text, error, provider}`, `provider` fixed to `"watsonx.ai"` until `ChatProvider` exists); CORS now allows `POST` | `SummaryPanel` | done |
| 5 | ~~`/api/stream`'s gate check hardcodes 80%~~ — fixed, `gate_threshold` query param (default 80.0), same as `/api/analyze` | live-progress gate readout | done |
| 6 | Partially fixed — `/api/summary` returns `provider`, fixed to `"watsonx.ai"` (the only provider that exists) | future Autofix result view; `provider` becomes dynamic | backend, once `ChatProvider` exists — source `provider` from it, and add the field to gap 3's future response |

## Deliverables

| Deliverable | Description | Status |
|---|---|---|
| Next.js app scaffold | New `web-next/`, calling the existing FastAPI backend, not replacing it | 🟢 |
| `RepoForm` + `ActionBar` | Repo path input, mutation/endpoints/threshold options, Analyze + Gate buttons (Autofix disabled — gap 3) | 🟢 |
| `StreamLog` | Live progress from `/api/stream`, rendering only the event types it actually emits (coverage/gaps/risk) | 🟢 |
| `StatCards` + `GapsList` + `RiskTable` | Coverage, mutation score, gaps, risk ranking — sourced verbatim from `AnalyzeResponse`, no new numbers invented | 🟢 |
| `SummaryPanel` | AI prose, labeled advisory + which provider generated it — calls `POST /api/summary` (PR #26 front, PR #27 back) | 🟢 |
| Vercel deploy | Connect repo/subfolder to Vercel; no IaC, config lives in `vercel.json` / project settings; `NEXT_PUBLIC_REPOGUARD_API_BASE` env var per environment | 🔴 |
| Docs | Fold this file and `docs/ARCHITECTURE-front.md` back into `PENDING.md`/`docs/ARCHITECTURE.md`, update `README.md`, once built | 🔴 |
| CI split | `frontend-ci.yml` (lint+build, `web-next/**` paths only) separate from backend `ci.yml`/`cd.yml` (now `paths-ignore: web-next/**`) — monorepo stays one repo per hackathon rules, but front/back CI runs never trigger each other | 🟢 |

**Verified so far:** `npm run lint` and `npm run build` both pass; `next dev`
was run directly and served the real page (200, title "TestMind AI").
Backend side of the summary contract verified against a real `repoguard
serve`: `POST /api/summary` with a real `/api/analyze` dashboard returns
`ok=false` + the credentials error when no `WATSONX_*` vars are set, and the
CORS preflight from `localhost:3000` allows `POST` + `content-type`. Not yet
verified: a browser run of `web-next` against a live `repoguard serve`
(both servers up at once), or a real summary generated with IBM Cloud
credentials.
