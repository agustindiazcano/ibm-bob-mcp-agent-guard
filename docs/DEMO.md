# TestMind AI — 3-Minute Demo Script

Two ways to show this: the **live public demo** (no setup, just a browser —
use this one) and a **local CLI walkthrough** for the parts the public demo
doesn't expose yet (autofix, mutation on a live click). Real, measured
numbers throughout — nothing here is invented; see `AGENTS.md §7`.

---

## Part A — Live demo (browser only, ~2 minutes)

- Dashboard: **https://ibm-bob-mcp-agent-guard.vercel.app/**
- Backend: `https://repoguard-ljm5hefnsq-uc.a.run.app` (Cloud Run, provider
  `vertex`)

> Cloud Run scales to zero when idle. If the very first click seems to hang
> or errors with "Can't reach the backend," that's a cold start (10-20s) —
> reload once. Hit the site yourself ~5 minutes before presenting to warm it
> up, or ask about setting `--min-instances=1` for the day.

### 1. The pitch, in one line

*"Coverage tells you what ran. Mutation testing tells you what your tests
would actually catch."*

### 2. Analyze the bundled fixture

Type `./demo-repo` (or leave the default), click **Analyze**.

Expected, live-verified numbers:

| Metric | Value |
|---|---|
| Coverage | 65.1% (112/172 lines) |
| Gap files | 4 (`pricing.py`, `cart.py`, `inventory.py`, `api.py`) |
| Endpoints tested | 1 / 7 |
| Gate (80% threshold) | **FAIL** |

Point at the gap list and risk table — coverage looks decent, but the risk
ranking already shows where a bug could hide untested.

### 3. Turn on mutation testing

Tick the mutation checkbox, re-run (or use a repo you've pre-warmed — a full
79-mutant pass takes a couple of minutes).

| Metric | Value |
|---|---|
| Mutation score | **20.25%** (16 / 79 mutants killed) |

*"65% coverage, but only 20% of injected bugs get caught. That 45-point gap
is the whole reason this tool exists — coverage was lying."*

### 4. AI summary (multicloud story)

Click **Summary**. This calls Google Vertex AI (`gemini`) against the
already-measured numbers above — advisory prose only, it never invents a
metric. The backend also supports IBM watsonx.ai as a second provider
(`docs/MULTICLOUD_AI.md`) behind the same `ChatProvider` interface — mention
it even if the live demo only shows one at a time.

### 5. (If ready) Autofix

`POST /api/fix` is built and tested (`verify.py phase14fix`) but disabled on
the public demo by default — it spends real AI-provider quota per run. If a
`REPOGUARD_FIX_TOKEN` was attached for this session, click **Autofix** and
narrate: writes tests only under `tests/` through a hard-guarded tool, never
touches source, real before/after mutation numbers. If the token isn't
attached, skip this and go to Part B, or narrate it from a recording.

### 6. (Coming soon) Swarm mode

If asked "can it go faster/parallel": the sequential fix loop above already
works end to end; a parallel multi-agent version (one lane per file,
concurrent) is in progress (Phase 18) — record a separate clip when it lands
rather than promising it live.

---

## Part B — Local CLI: the full before/after (optional, ~1 minute, needs setup)

Shows the "after" jump the public demo doesn't have history for yet.

```bash
pip install -e ".[dev]"
cd demo-repo && python -m pytest -q   # 5 passed
cd ..
repoguard analyze ./demo-repo --mutation
# coverage 65.1%, mutation 20.25% (16/79) -- matches Part A exactly
```

Reveal the "after" state using the hand-written reference tests (never
leave these in `demo-repo/tests/` afterward — see `AGENTS.md §7`):

```bash
cp docs/expected-after-tests/*.py demo-repo/tests/
repoguard analyze ./demo-repo --mutation
# 71 passed, coverage 100%, mutation 89.87% (71/79), 7/7 endpoints tested
rm demo-repo/tests/test_*_complete.py   # restore the baseline immediately after
```

| | Before | After |
|---|---|---|
| Coverage | 65.1% | 100% |
| Mutation score | 20.25% (16/79) | 89.87% (71/79) |
| Endpoints tested | 1/7 | 7/7 |
| Gate (80%) | FAIL | PASS |

To show the AI *writing* those tests itself instead of a pre-written
reference set, run the real fix loop (needs credentials —
`docs/WATSONX_SETUP.md` or `docs/VERTEX_SETUP.md`):

```bash
repoguard fix ./demo-repo --provider vertex
# writes tests through the guarded write_test_file tool (tests/ only),
# critiques them, re-measures for real, writes demo-repo/watson-evidence/
```

Without credentials this fails immediately with a clear error, on purpose —
before the multi-minute mutation baseline would otherwise run for nothing.

---

## Fallback if the live site is down

Run `repoguard serve` locally and open `http://localhost:8000` — same UI,
same measured numbers, `REPOGUARD_AI_PROVIDER` defaults to whichever
credentials are in your local environment.
