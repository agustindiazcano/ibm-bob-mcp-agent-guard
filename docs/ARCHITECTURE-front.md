# Frontend architecture: Next.js dashboard on Vercel

**Satellite doc — kept separate from `docs/ARCHITECTURE.md` on purpose, so
frontend and backend work can each land without fighting over the same
paragraphs of a shared file. Same pattern `docs/MULTICLOUD_AI.md` uses for
the AI-provider layer. `docs/ARCHITECTURE.md`'s "Next.js dashboard on
Vercel" section is a short summary pointing here.**

**Status: built in `web-next/` and deployed to Vercel
(https://ibm-bob-mcp-agent-guard.vercel.app/). Still open: pointing the
deployment at a real backend, and Autofix — tracker in
`PENDING.md` Phase 14.**

The original web UI (`web/static/index.html`, served by `web/server.py`)
stays as the reference implementation. `web-next/` is a separate, richer
frontend consuming the same FastAPI endpoints rather than replacing them:

```
┌───────────────────────────────┐        ┌───────────────────────────────┐
│  Next.js dashboard (Vercel)   │  HTTP  │  repoguard_engine/web/server  │
│  stats, gaps, risk table,     │ ─────▶ │  (FastAPI)                    │
│  AI summary, Analyze / Gate   │  + SSE │  /api/analyze · /api/stream   │
│                               │        │  /api/summary                 │
└───────────────────────────────┘        └───────────────────────────────┘
```

No Terraform, no GCP-specific IaC for this piece — Vercel builds and hosts
the Next.js app directly from the repo. This doesn't change the Cloud Run CD
pipeline (`docs/DEPLOY.md`, Phase 13); the Next.js app is an additional
frontend, not a replacement backend deploy target.

## Routes (App Router)

The engine has no persistence layer yet (run history is Phase 17, design
only), so a "run" only exists as client state for the life of the browser
tab — one route:

| Route | Purpose |
|---|---|
| `/` | Repo-path input, action bar, live stream log, stat cards, gaps list, risk table, AI summary panel |

A `/report/[id]` history route needs a backend store for past runs; it
belongs to Phase 17 (`docs/DATA_PLATFORM.md`), not this phase.

## Component breakdown (`web-next/app/`)

| Component | Renders | Fed by |
|---|---|---|
| `RepoForm` | repo path input, mutation checkbox, gate threshold input | user input only |
| `ActionBar` | "Analyze" and "Gate" buttons; "Autofix" ships disabled (gap 3 below) | triggers the calls below |
| `StreamLog` | live progress lines as SSE events arrive | `/api/stream` |
| `StatCards` | coverage % (covered/total lines), mutation score or "Not run", files with gaps, gate PASS/FAIL with the threshold that run used | `AnalyzeResponse` + the submitted threshold |
| `GapsList` | uncovered files + missing lines | `AnalyzeResponse.gaps` |
| `RiskTable` | file + reasons, score with a bar (the score is already a 0–1 uncovered-line ratio, so the bar width is the score itself) | `AnalyzeResponse.risk` |
| `Card` | shared section frame (title, optional badge) | — |

Styling is CSS Modules next to each component plus design tokens in
`app/globals.css` (light and dark via `prefers-color-scheme`), no CSS
dependency. Formatting is display-only (`toFixed`, same decimals everywhere);
no component derives a new metric.
| `SummaryPanel` | AI prose, labeled "advisory, not a measurement", plus which provider generated it; "Summary unavailable: …" when `ok=false` | `SummaryResponse`, passed in by `page.tsx` |

`page.tsx` owns all fetching. One Analyze click opens the `/api/stream`
`EventSource` and calls `/api/analyze` in parallel; once `/api/analyze`
returns, it requests `/api/summary` once, not awaited, so the summary never
delays or fails the dashboard. It is deliberately not fetched from a
`SummaryPanel` effect: React StrictMode runs effects twice in dev, which made
two paid AI calls per local run. A run counter drops a summary that arrives
after a newer Analyze click.

## Data contract — reuse verbatim, never reshape

Per `AGENTS.md §4` (the engine measures, the AI never invents a number), the
frontend treats these as pass-through types (`web-next/app/lib/types.ts`) —
it renders them, it never recomputes or reinterprets a number client-side.

`GET /api/analyze?repo_path=&mutation=&gate_threshold=` returns:

```ts
type AnalyzeResponse = {
  coverage: { percent: number; covered_lines: number; total_lines: number };
  gaps: { uncovered_files: string[]; missing_lines_by_file: Record<string, number[]> };
  mutation: { score: number; killed: number; survived: number; total: number } | null; // null unless mutation=true
  risk: { file: string; score: number; reasons: string[] }[];
  passed_gate: boolean;
};
```

`GET /api/stream?repo_path=&gate_threshold=` emits SSE frames
`{"type": ..., "data": ...}` with types
`start | progress | coverage | gaps | risk | done | error`. It only covers
coverage/gaps/risk — never mutation or endpoints — so `StreamLog` renders
whatever the stream actually sends and doesn't assume it mirrors
`/api/analyze`'s full shape. The stream runs its own measurement alongside
`/api/analyze`'s; `measure_coverage()` uses a per-run temp dir, so the two
concurrent pytest-cov runs don't overwrite each other's data.

`POST /api/summary`, body: the `AnalyzeResponse` above, returns:

```ts
type SummaryResponse = {
  ok: boolean;
  text: string;     // advisory prose, only when ok=true
  error: string;    // real error, only when ok=false (e.g. missing credentials)
  provider: string; // "watsonx" | "vertex" — the provider actually used, set on both paths
};
```

`ok=false` is an expected state, not a bug: it's what every deployment
without AI credentials returns. The panel shows the error and the rest of
the dashboard is unaffected.

## AI providers

The backend has two AI providers behind `ai_providers.get_provider()`
(`docs/MULTICLOUD_AI.md`): watsonx.ai (default) and Google Vertex AI,
selected server-side by `REPOGUARD_AI_PROVIDER`. The CLI also has a
per-call `--provider` flag, but `/api/summary` doesn't take one, so the
frontend has no provider selector — the provider is a deploy-time backend
choice, and `SummaryPanel` only displays the `provider` it's told.
Credentials (watsonx API key, `GOOGLE_APPLICATION_CREDENTIALS`) stay
server-side only; the frontend never holds or forwards one.

## Backend gaps this phase depended on

| # | Gap | Status |
|---|---|---|
| 1 | CORS — `REPOGUARD_CORS_ORIGINS` (default `localhost:3000` and `127.0.0.1:3000` only — the Vercel domain must be added when the backend is deployed), `GET` + `POST`, all headers | 🟢 |
| 2 | Gate — no new endpoint needed, `/api/analyze?gate_threshold=N` returns `passed_gate` | 🟢 |
| 3 | No `POST /api/fix` — the fix loop (`repoguard fix`) is CLI-only | 🔴 Autofix stays disabled. Exposing it means a long-running, credentialed, possibly PR-opening action over HTTP — auth and rate limiting the read-only endpoints never needed. Build it after a verified live fix-loop run (Phase 11); `ChatProvider` (Phase 16) is already done |
| 4 | `POST /api/summary` | 🟢 PR #27 |
| 5 | `/api/stream` takes `gate_threshold` instead of a hardcoded 80% | 🟢 PR #27 |
| 6 | `provider` surfaced in responses | 🟢 on `/api/summary`, from the provider actually used; add it to gap 3's endpoint when that exists |

## Local dev & deployment config

- `web-next/.env.local` (copy `.env.example`):
  `NEXT_PUBLIC_REPOGUARD_API_BASE=http://127.0.0.1:8000`, matching
  `repoguard serve`'s default host/port.
- Vercel project env var: `NEXT_PUBLIC_REPOGUARD_API_BASE=<Cloud Run URL>`.
  Today it's a `localhost:8000` placeholder, so the deployed page loads but
  can't analyze anything until the backend is on Cloud Run (Phase 13) and
  its origin is added to `REPOGUARD_CORS_ORIGINS`.
- No secrets live in the Next.js app. It only calls the backend's endpoints
  with a repo path the user types in.
