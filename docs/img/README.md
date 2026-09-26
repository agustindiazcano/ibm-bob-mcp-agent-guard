# docs/img — images used by the README

| File | What it is | How to regenerate |
|---|---|---|
| `results-en-light.png`, `results-en-dark.png` | Before/after results chart | `python docs/make_results_chart.py` |
| `dashboard-light.png`, `dashboard-dark.png` | `web-next/` dashboard after Analyze with mutation testing on `demo-repo` | See below |

Dashboard screenshots are real captures, not mockups. To retake them: start
`repoguard serve --port 8010` (on Windows with `PYTHONIOENCODING=utf-8`),
build and start `web-next/` with
`NEXT_PUBLIC_REPOGUARD_API_BASE=http://localhost:8010 npm run build && npm start`
(a production build, so the dev-mode indicator isn't in the shot), check
"Run mutation testing", press Analyze on `./demo-repo`, and capture the full
page at 1280px wide in light and dark color schemes. The numbers must match
`AGENTS.md §7` (coverage 65.1%, mutation 20.25%, 16/79).
