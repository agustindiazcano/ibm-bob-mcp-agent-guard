# docs/img — images used by the README

| File | What it is | How to regenerate |
|---|---|---|
| `results-en-light.png`, `results-en-dark.png` | Before/after results chart | `python docs/make_results_chart.py` |
| `dashboard-light.png`, `dashboard-dark.png` | `web-next/` dashboard after Analyze with mutation testing on `demo-repo` | See below |
| `demo-intro.png`, `demo-autofix.png`, `demo-results.png` | `web-next/` in Demo Mode: intro slide, Autofix replay, Results for `demo-showcase` | See "Demo Mode screenshots" below |

Dashboard screenshots are real captures, not mockups. To retake them: start
`repoguard serve --port 8010` (on Windows with `PYTHONIOENCODING=utf-8`),
build and start `web-next/` with
`NEXT_PUBLIC_REPOGUARD_API_BASE=http://localhost:8010 npm run build && npm start`
(a production build, so the dev-mode indicator isn't in the shot), check
"Run mutation testing", press Analyze on `./demo-repo`, and capture the full
page at 1280px wide in light and dark color schemes. The numbers must match
`AGENTS.md §7` (coverage 65.1%, mutation 20.25%, 16/79).

## Demo Mode screenshots

`npx next dev -p 3100` in `web-next/`, then Playwright (Chrome channel,
1440×900, dark) with `localStorage.testmind_demo_mode = "true"` set by an init
script: `/intro` (viewport), `/` after clicking Autofix and waiting for "Demo
Mode — simulated timing" (full page), and `/results` with `demo-showcase`
selected (full page). The Next dev badge, the site footer and the fixed
"built with" bar are hidden with injected CSS. Reach `/results` by clicking
its nav link from `/`, not by loading it directly: a direct load races the
real `/api/projects` fetch against the demo data and can show "No projects".
The `/swarm` slide isn't used in the README: its lane numbers are
illustrative, not measured.
