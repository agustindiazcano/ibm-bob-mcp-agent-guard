# web-next

Next.js frontend for TestMind AI, deployed at
https://ibm-bob-mcp-agent-guard.vercel.app/. Calls the existing FastAPI
backend (`repoguard_engine/web/server.py`) over HTTP/SSE — it never replaces
it and never talks to Python directly. See `../docs/ARCHITECTURE-front.md`
for the data contract and `../PENDING.md` Phase 14 for status.

## Local dev

```bash
cp .env.example .env.local   # NEXT_PUBLIC_REPOGUARD_API_BASE, defaults to 127.0.0.1:8000
npm install
npm run dev                  # http://localhost:3000
```

Run the backend alongside it from the repo root with `repoguard serve`
(port 8000). Its CORS allows `http://localhost:3000` by default; set
`REPOGUARD_CORS_ORIGINS` to allow any other origin. On Windows, start it
with `PYTHONIOENCODING=utf-8`, or the console output crashes it on startup.
If the page can't reach the backend, it says so and names the URL it tried
(a stopped backend and a CORS rejection look identical to the browser).

Without AI credentials on the backend, the summary panel shows "Summary
unavailable: …" — expected, not a bug. See `../docs/WATSONX_SETUP.md` or
`../docs/VERTEX_SETUP.md` to get a real summary.

## Deploy (Vercel)

Production talks to the Cloud Run backend through
`NEXT_PUBLIC_REPOGUARD_API_BASE=https://repoguard-ljm5hefnsq-uc.a.run.app`
(Vercel → Settings → Environment Variables; keep the `NEXT_PUBLIC_` prefix,
type "Config"). The value is baked in at build time: after changing it,
Redeploy the **newest `main`** deployment — redeploying an older one ships
old code. Merges to `main` deploy automatically. Details and the CORS side:
`../docs/ARCHITECTURE-front.md` → "Local dev & deployment config".

## Structure

```text
web-next/
├── app/
│   ├── components/       # Reusable UI components (RepoForm, StatCards, etc.)
│   ├── lib/              # API clients, data fetching, types
│   ├── results/          # Historical measurement dashboard (/results)
│   ├── layout.tsx        # Root layout
│   └── page.tsx          # Main dashboard route (/)
├── public/               # Static assets
├── .env.example          # Environment variables template
├── package.json          # Dependencies and scripts
└── README.md             # This file
```

| Path | Purpose |
|---|---|
| `app/page.tsx` | Main route (`/`): owns all fetching — stream, analyze, then one summary request per run |
| `app/components/` | `RepoForm`, `ActionBar`, `StreamLog`, `StatCards`, `GapsList`, `RiskTable`, `EndpointsList`, `SummaryPanel`, `Card` — render props only, each with its own CSS Module |
| `app/results/` | Route (`/results`): historical measurement dashboard. `history.ts` fetches from `/api/projects/` routes, `ResultsDashboard` organizes the charts |
| `app/lib/types.ts` | `AnalyzeResponse`, `SummaryResponse`, SSE event types — mirror `web/server.py` verbatim, never reshaped |
| `app/lib/api.ts` | `fetchAnalyze`, `fetchSummary`, `streamUrl` against `NEXT_PUBLIC_REPOGUARD_API_BASE` |

The Autofix button is intentionally disabled — no `POST /api/fix` yet
(backend gap 3 in `../PENDING.md` Phase 14).

## Checks

`npm run lint && npm run build` — the same two steps
`.github/workflows/frontend-ci.yml` runs on every change under `web-next/`.
