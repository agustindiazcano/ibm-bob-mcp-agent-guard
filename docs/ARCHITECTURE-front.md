# Frontend architecture: Next.js dashboard on Vercel

**Satellite doc — kept separate from `docs/ARCHITECTURE.md` on purpose, so
frontend work (this branch, `feat/14-nextjs-dashboard-arch`) and backend
work (e.g. the watsonx/multicloud migration) can each land without fighting
over the same paragraphs of a shared file. Same pattern `docs/MULTICLOUD_AI.md`
already uses for the AI-provider refactor. Fold the relevant parts into
`docs/ARCHITECTURE.md`'s "Planned: Next.js dashboard on Vercel" section at
merge time — see `README.md`/`PENDING.md`'s own note pointing here.**

**Not built yet — roadmap only, see `PENDING-front.md`.**

The current web UI (`web/static/index.html`, served by `web/server.py`)
stays as the reference implementation. The plan is a richer frontend, built
separately in a new `web-next/` app and consuming the same FastAPI endpoints
rather than replacing them:

```
┌───────────────────────────────┐        ┌──────────────────────────────┐
│  Next.js dashboard (Vercel)   │  HTTP  │  repoguard_engine/web/server  │
│  charts, risk table, action   │ ─────▶ │  (FastAPI)                    │
│  buttons ("Analyze", "Gate")  │  + SSE │  /api/analyze · /api/stream   │
└───────────────────────────────┘        └──────────────────────────────┘
```

No Terraform, no GCP-specific IaC for this piece — Vercel builds and hosts
the Next.js app directly from the repo. This doesn't change the existing
Cloud Run CD pipeline (`docs/DEPLOY.md`, Phase 13); the Next.js app is an
additional frontend, not a replacement backend deploy target.

## Routes (App Router)

There's no persistence layer (no DB, no run history) anywhere in the engine,
so a "run" only exists as client state for the life of the browser tab — one
route covers v1:

| Route | Purpose |
|---|---|
| `/` | Repo-path input, action bar, live stream log, stat cards, gaps list, risk table, AI summary panel |

A `/report/[id]` history route is explicitly **not** planned for v1 — it
would need a backend store for past runs, which doesn't exist and is out of
scope for a frontend-only phase.

## Component breakdown (`web-next/app/`)

| Component | Renders | Fed by |
|---|---|---|
| `RepoForm` | repo path input, mutation/endpoints checkboxes, gate threshold input | user input only |
| `ActionBar` | "Analyze" and "Gate" buttons ("Autofix" ships disabled — see gap 3 below) | triggers the fetch/`EventSource` calls below |
| `StreamLog` | live progress lines as SSE events arrive | `/api/stream` |
| `StatCards` | coverage %, mutation score, risk count | `dashboard.coverage`, `dashboard.mutation` |
| `GapsList` | uncovered files + missing lines | `dashboard.gaps` |
| `RiskTable` | file, score, reasons, sorted desc | `dashboard.risk` |
| `SummaryPanel` | AI prose, labeled "advisory, not a measurement", plus which provider generated it | needs a summary HTTP path — see gap 4 below |

## Data contract — reuse verbatim, never reshape

Per `AGENTS.md §4` (the engine measures, the AI never invents a number), the
frontend treats these as opaque pass-through types — it renders them, it
never recomputes or reinterprets a number client-side.

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

`GET /api/stream?repo_path=` emits SSE frames `{"type": ..., "data": ...}`
with types `start | progress | coverage | gaps | risk | done | error`.
**It only ever covers coverage/gaps/risk today** — never mutation or
endpoints — so `StreamLog`/`StatCards` must render whatever the stream
actually sends, not assume it mirrors `/api/analyze`'s full shape.

Neither of these types changes because of multicloud (below) —
`AnalyzeResponse` and the SSE stream are pure measurement, and
`docs/MULTICLOUD_AI.md` is explicit that "measurement is unaffected either
way" regardless of which AI provider is configured.

## AI provider awareness (future — design only, nothing built)

`docs/MULTICLOUD_AI.md` is adding a second AI provider — Google Vertex AI
alongside watsonx.ai — behind a `ChatProvider` protocol, selected
server-side via `REPOGUARD_AI_PROVIDER` (or possibly a per-call `--provider`
flag; still an open question in that doc, not decided). This affects two
things the frontend will eventually surface, once the endpoints in gaps 3–4
below exist — nothing to build yet:

- **`SummaryPanel`** should show which provider produced the prose (e.g. "via
  watsonx.ai" / "via Vertex AI"), so the advisory-text label stays honest
  about its source, not just that it's advisory.
- **If** `REPOGUARD_AI_PROVIDER` becomes a per-request flag rather than a
  fixed server env var, `RepoForm`/`ActionBar` would need a provider selector
  for Autofix/Summarize. **If** it stays a single process-wide env var
  (today's design), the frontend needs nothing extra — it's a deploy-time
  backend choice, invisible to any one request. Don't build a selector until
  that open question resolves.
- Either way, provider credentials (watsonx API key,
  `GOOGLE_APPLICATION_CREDENTIALS`) stay server-side only, same rule as
  today — the frontend never holds or forwards a credential for either
  cloud.

Proposed shape for the still-unbuilt summary endpoint (gap 4), once it
exists — not implemented, for discussion only:

```ts
type SummaryResponse =
  | { ok: true; text: string; provider: "watsonx" | "vertex" }
  | { ok: false; error: string };
```

## Backend gaps this plan depends on

Not this phase's work (no engine/API changes here — Phase 14 is
frontend-only), but the frontend can't be built truthfully against
endpoints that don't exist or don't do what the roadmap prose implies.
Recording them so the dependency is explicit instead of discovered
mid-build:

1. **No CORS.** `web/server.py` has no `CORSMiddleware`. A Vercel-hosted
   origin calling the Cloud Run backend is cross-origin by construction —
   `allow_origins` for the Vercel domain(s) has to exist before the frontend
   can call it at all.
2. **"Gate" needs no new endpoint.** `/api/analyze` already accepts
   `gate_threshold` and returns `passed_gate` — the Gate button is just
   `/api/analyze?gate_threshold=N`.
3. **"Autofix" has no HTTP endpoint.** The fix loop (`repoguard fix`,
   `watson_agent/orchestrator.py`) is CLI-only — as of this writing that
   module (and the multicloud `ai_providers/` refactor on top of it, see
   above) is still in progress on a separate branch, not yet on `main`;
   re-check `AGENTS.md §2` and `docs/MULTICLOUD_AI.md` before building
   against it. There is no `POST /api/fix`, and adding one means exposing a
   long-running, credentialed, potentially PR-opening action over HTTP —
   auth and rate-limiting questions the read-only endpoints never had to
   answer. **Decision for whoever builds this phase:** ship v1 with the
   Autofix button disabled ("coming soon"), rather than couple the frontend
   launch to an unreviewed credentialed endpoint. Revisit once the fix loop
   *and* the multicloud provider abstraction are both stable — building the
   endpoint before `ChatProvider` lands would just mean redoing it once a
   second provider exists.
4. **No summary endpoint.** `tool_generate_summary` / `generate_summary()`
   exist only as an MCP tool and a CLI flag (`analyze --summarize`) — no
   `/api/analyze?summarize=true` or dedicated route. `SummaryPanel` can't
   ship until one is added to `web/server.py`. Same sequencing note as gap
   3: whoever adds this endpoint should do it after (or alongside)
   `ai_providers.get_provider()` lands, so it returns `provider` from day
   one instead of hardcoding `"watsonx"` and needing a second migration.
5. **`/api/stream`'s gate check is hardcoded.** `_stream_pipeline` checks
   `coverage.percent >= 80.0` literally and never accepts a `gate_threshold`
   query param. `StreamLog` must not treat `done.passed_gate` as
   authoritative for a custom threshold — re-check via `/api/analyze` once
   the stream finishes, until this is fixed.
6. **No provider surfaced anywhere yet.** Neither `narrative.py` nor
   `watson_agent/orchestrator.py` currently return which AI backend ran —
   there's only ever been one (watsonx.ai). Once `ai_providers/base.py`'s
   `ChatProvider` exists (`docs/MULTICLOUD_AI.md` step 2), gaps 3 and 4's
   future endpoints should include a `provider` field in their response so
   `SummaryPanel` (and, later, an Autofix result view) can label their
   output honestly instead of the frontend guessing or hardcoding a name.

## Local dev & deployment config

- `web-next/.env.local`: `NEXT_PUBLIC_REPOGUARD_API_BASE=http://127.0.0.1:8000`
  (matches `repoguard serve`'s default host/port).
- Vercel project env var: `NEXT_PUBLIC_REPOGUARD_API_BASE=<Cloud Run URL>`
  (from `docs/DEPLOY.md`'s Phase 13 setup) for preview/prod environments.
- No secrets live in the Next.js app. It only ever calls the backend's
  already-public read endpoints (once CORS is opened) with a repo path the
  user types in; watsonx/Vertex credentials stay server-side and never reach
  the browser.
