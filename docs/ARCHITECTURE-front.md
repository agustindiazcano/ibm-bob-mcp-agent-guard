# Frontend architecture: Next.js dashboard on Vercel

**Satellite doc — kept separate from `docs/ARCHITECTURE.md` on purpose, so
frontend and backend work can each land without fighting over the same
paragraphs of a shared file. Same pattern `docs/MULTICLOUD_AI.md` uses for
the AI-provider layer. `docs/ARCHITECTURE.md`'s "Next.js dashboard on
Vercel" section is a short summary pointing here.**

**Status: built in `web-next/`, deployed to Vercel
(https://ibm-bob-mcp-agent-guard.vercel.app/) and wired to the real backend
on Cloud Run (`https://repoguard-ljm5hefnsq-uc.a.run.app`) — Analyze works
end to end on the public URL, including the AI summary (`ok=true` via
Vertex). Autofix (`POST /api/fix`, gap 3) is built; it's still waiting on
the token being attached on Cloud Run and a first live run.**

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
| `RepoForm` | repo path input, mutation checkbox, gate threshold input, Autofix token (password field, kept in React state only) | user input only |
| `ActionBar` | "Analyze", "Gate" and "Autofix" buttons (Autofix enabled once a token is entered) | triggers the calls below |
| `StreamLog` | live progress lines as SSE events arrive | `/api/stream` |
| `StatCards` | coverage % (covered/total lines), mutation score or "Not run", files with gaps, gate PASS/FAIL with the threshold that run used | `AnalyzeResponse` + the submitted threshold |
| `GapsList` | uncovered files + missing lines | `AnalyzeResponse.gaps` |
| `RiskTable` | file + reasons, score with a bar (the score is already a 0–1 uncovered-line ratio, so the bar width is the score itself) | `AnalyzeResponse.risk` |
| `SummaryPanel` | AI prose, labeled "advisory, not a measurement", plus which provider generated it; "Summary unavailable: …" when `ok=false` | `SummaryResponse`, passed in by `page.tsx` |
| `FixResultPanel` | Autofix: engine-measured before → after (mutation, coverage), test files written (expandable), critic notes labeled advisory, provider | `/api/fix`'s `done` event |
| `Card` | shared section frame (title, optional badge) | — |

Styling is CSS Modules next to each component plus design tokens in
`app/globals.css` (light and dark via `prefers-color-scheme`), no CSS
dependency. Formatting is display-only (`toFixed`, same decimals everywhere);
no component derives a new metric.

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

**Errors** (`web-next/app/lib/api.ts`): every call goes through `request()`.
A network failure becomes "Can't reach the backend at `<API base>`…",
naming both likely causes, because a stopped backend and a CORS rejection
reach the browser as the same opaque `TypeError`. A non-2xx response shows
FastAPI's `detail` when the body has one (e.g. `/api/analyze`'s 400 for a
nonexistent `repo_path`), else `"<call> failed: <status>"` — note that over
HTTP/2 (Cloud Run) `statusText` is empty, so the status code is all there is.

**Autofix** (`POST /api/fix`, `web/fix_job.py`): the one endpoint that
spends AI quota and runs for minutes, so it differs from the rest:

- **Auth:** `Authorization: Bearer <token>` must match the server's
  `REPOGUARD_FIX_TOKEN`. If that variable isn't set, the endpoint is off
  (`503`); a missing or wrong token gets `401`. A static site can't keep a
  secret, so the token is typed into a password field and never stored.
- **One run per process:** a second request while one is running gets
  `409`.
- **Sandbox:** the fix loop runs on a temp copy of `repo_path` with
  `publish=False`. The target repo is never modified, and nothing is
  committed or pushed. The copy is deleted after the run, and the tests it
  wrote come back in the response.
- **Transport:** one long request streaming `application/x-ndjson`, one
  `{type, data}` object per line, read with `fetch` + `ReadableStream`
  (`streamFix()` in `api.ts`). `EventSource` can't POST or send headers.
  Heartbeats go out every 15 s during silent stretches, such as a mutation
  run. Cloud Run's request timeout is raised to 1800 s in `cd.yml`.

Event types, in order: `start` → `baseline_start` → `baseline_done` →
(`writer_start` → `critic_start`) per file → `remeasure_start` →
`remeasure_done` → `done`, or `error` at any point. `heartbeat` can appear
anywhere. The `done` event's data:

```ts
type FixDone = {
  provider: string;            // "watsonx" | "vertex", the provider actually used
  before: Dashboard;           // engine-measured, verbatim
  after: Dashboard | null;     // engine-measured, verbatim
  files_attempted: string[];
  files: { path: string; status: "added" | "modified"; content: string }[];
  critic_notes: string[];      // advisory model output, not a measurement
  evidence: string;            // the watson-evidence/NN-fix-loop.md report
};
```

## AI providers

The backend has two AI providers behind `ai_providers.get_provider()`
(`docs/MULTICLOUD_AI.md`): watsonx.ai (default) and Google Vertex AI,
selected server-side by `REPOGUARD_AI_PROVIDER`. The CLI also has a
per-call `--provider` flag, but `/api/summary` doesn't take one, so the
frontend has no provider selector — the provider is a deploy-time backend
choice, and `SummaryPanel` only displays the `provider` it's told.
Credentials (watsonx API key, `GOOGLE_APPLICATION_CREDENTIALS`) stay
server-side only; the frontend never holds or forwards one.

On Cloud Run the chosen provider is Vertex (`REPOGUARD_AI_PROVIDER=vertex`,
`VERTEX_PROJECT_ID` set on the service). Vertex needs no secret there — it
authenticates as the service's runtime account, which has
`roles/aiplatform.user`. The public demo's summary still shows
"unavailable" until the image includes the `[vertex]` extra
(`fix/vertex-import-error-detail`, `PENDING.md` Phase 14 gap 8). Nothing
changes in the frontend once that ships.

## Backend gaps this phase depended on

| # | Gap | Status |
|---|---|---|
| 1 | CORS — `REPOGUARD_CORS_ORIGINS` (default `localhost:3000` and `127.0.0.1:3000`; Cloud Run sets the Vercel domain in `cd.yml`, PR #49), `GET` + `POST`, all headers | 🟢 |
| 2 | Gate — no new endpoint needed, `/api/analyze?gate_threshold=N` returns `passed_gate` | 🟢 |
| 3 | `POST /api/fix` (Autofix) | 🟡 built — token-gated, one run at a time, sandboxed, streamed as NDJSON (contract above). Needs `REPOGUARD_FIX_TOKEN` attached on Cloud Run (`docs/DEPLOY.md` §5) and a first live run |
| 4 | `POST /api/summary` | 🟢 PR #27 |
| 5 | `/api/stream` takes `gate_threshold` instead of a hardcoded 80% | 🟢 PR #27 |
| 6 | `provider` surfaced in responses | 🟢 on `/api/summary` and on `/api/fix`'s `done` event, from the provider actually used |
| 7 | Nonexistent `repo_path` → raw 500 | 🟢 400 with a `detail` message (PR #47) |
| 8 | AI summary on Cloud Run (Vertex SDK in the image; runtime-account role granted) | 🟢 PR #52, verified live (`ok: true`, `provider: vertex`) |

## Local dev & deployment config

- `web-next/.env.local` (copy `.env.example`):
  `NEXT_PUBLIC_REPOGUARD_API_BASE=http://127.0.0.1:8000`, matching
  `repoguard serve`'s default host/port.
- Vercel (Settings → Environment Variables):
  `NEXT_PUBLIC_REPOGUARD_API_BASE=https://repoguard-ljm5hefnsq-uc.a.run.app`,
  no trailing slash (`api.ts` appends `/api/...`), Production + Preview.
  Vercel warns that the `NEXT_PUBLIC_` prefix exposes the value to the
  browser — that's intended, the browser calls this URL directly; keep the
  prefix and mark it "Config". Removing the prefix leaves it undefined in
  the browser.
- **`NEXT_PUBLIC_*` is inlined at build time.** Saving a new value changes
  nothing until a new build runs. Redeploy the **newest `main`** deployment;
  redeploying or promoting an older row ships that row's old code (this
  happened: it rolled production back to pre-#48 code, and once to a
  `127.0.0.1:8000` build). To check what's live, search the served JS for
  the API base URL. Normal merges to `main` redeploy automatically.
- Cloud Run: `REPOGUARD_CORS_ORIGINS=https://ibm-bob-mcp-agent-guard.vercel.app`
  comes from `cd.yml`'s `env_vars`. Vercel preview URLs
  (`…-git-<branch>-….vercel.app`) are not in it, so previews can't call the
  backend unless added.
- No secrets live in the Next.js app. It only calls the backend's endpoints
  with a repo path the user types in.
