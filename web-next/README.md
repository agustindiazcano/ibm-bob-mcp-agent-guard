# web-next

Next.js frontend for TestMind AI. Calls the existing FastAPI backend
(`repoguard_engine/web/server.py`) over HTTP/SSE — it never replaces it and
never talks to Python directly. See `../docs/ARCHITECTURE-front.md` and
`../PENDING.md` Phase 14 for the full plan and backend-gap tracker.

## Local dev

```bash
cp .env.example .env.local   # NEXT_PUBLIC_REPOGUARD_API_BASE, defaults to localhost:8000
npm install
npm run dev                  # http://localhost:3000
```

Run the backend alongside it from the repo root: `repoguard serve` (port
8000) needs `CORSMiddleware` allowing `http://localhost:3000` — see
`REPOGUARD_CORS_ORIGINS` in `repoguard_engine/web/server.py`.

## Structure

| Path | Purpose |
|---|---|
| `app/page.tsx` | Single route (`/`): repo form, action bar, live stream log, results |
| `app/components/` | `RepoForm`, `ActionBar`, `StreamLog`, `StatCards`, `GapsList`, `RiskTable`, `SummaryPanel` |
| `app/lib/types.ts` | `AnalyzeResponse`/SSE event types — mirror `web/server.py` verbatim, never reshaped |
| `app/lib/api.ts` | Fetch/EventSource helpers against `NEXT_PUBLIC_REPOGUARD_API_BASE` |

The Autofix button is intentionally disabled — no `POST /api/fix` yet
(backend gap 3 in `../PENDING.md` Phase 14).
