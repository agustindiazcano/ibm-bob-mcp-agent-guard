# README-front.md — Roadmap addendum: Next.js dashboard on Vercel

**Satellite doc — kept separate from `README.md`'s own Roadmap section on
purpose, so this branch doesn't fight the backend branch over the same
paragraph. Fold this into `README.md`'s "Roadmap" section at merge time.**

**Next up: a Next.js dashboard on Vercel.** The current web UI
(`repoguard serve`, `web/static/index.html`) stays as the reference
implementation and keeps serving `/api/analyze` and `/api/stream`. Planned
on top of it: a richer Next.js frontend — charts for coverage/mutation/risk,
a surviving-mutants table, and one-click buttons for "Analyze" and "Gate" —
deployed to Vercel, consuming the same FastAPI endpoints rather than
replacing them. An "Autofix" button ships disabled at first: it needs a new
`POST /api/fix` the backend doesn't have yet, and the backend's AI layer is
itself going multicloud (watsonx.ai + Google Vertex AI, design in
`docs/MULTICLOUD_AI.md`) — see `docs/ARCHITECTURE-front.md`'s gap list for
the sequencing.

We're deliberately not adopting Terraform or new GCP infrastructure for
this: the existing Cloud Run deploy (`docs/DEPLOY.md`, Phase 13) is left
as-is, and the new frontend ships as a plain Vercel project (no IaC). See
`PENDING-front.md` and `docs/ARCHITECTURE-front.md` for details. Not built
yet.
