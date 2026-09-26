# RepoGuard Demo Walkthrough

This demo uses the bundled `demo-repo/` fixture — a small e-commerce app with intentionally weak tests.

## Setup

```bash
pip install -e ".[dev]"
cd demo-repo
pip install fastapi httpx pytest pytest-cov
```

## Step 1 — See the baseline (bad coverage)

```bash
repoguard analyze ./demo-repo
```

Expected output:
- Coverage: ~25–35% (only the happy paths are tested)
- Risk files: `shop/pricing.py`, `shop/cart.py`, `shop/inventory.py`, `shop/api.py`

## Step 2 — Run the gate (it should fail)

```bash
repoguard gate ./demo-repo --threshold 80
# Exit code 1 — gate fails
```

## Step 3 — Start the web dashboard

```bash
repoguard serve
# Open http://localhost:8000
```

Enter `./demo-repo` in the path field and click Analyse or Stream.

## Step 4 — Run the watsonx.ai fix loop

Requires `WATSONX_APIKEY`/`WATSONX_PROJECT_ID` (`pip install -e ".[ai]"`, see `docs/WATSONX_SETUP.md`):

```bash
repoguard fix ./demo-repo
```

`repoguard_engine/watson_agent/orchestrator.py` will:
1. Measure a real baseline (coverage, mutation, gaps, risk)
2. Prioritize up to 3 files by risk score
3. Ask watsonx.ai to write a test per file, through the guarded `write_test_file` tool (`tests/` only)
4. Ask watsonx.ai to critique each new test
5. Re-measure for real and write the run report to `demo-repo/watson-evidence/`

Without credentials, this fails immediately with a clear error instead of silently doing nothing.

## Step 5 — Verify the gate now passes

```bash
repoguard gate ./demo-repo --threshold 80
# Exit code 0 — gate passes
```

## What the Demo Shows

| Before | After |
|---|---|
| ~30% coverage | ≥ 80% coverage |
| 3 tests, all happy-path | ~20 tests, edge cases + boundaries |
| Gate fails | Gate passes |
| Mutation score: unknown | Mutation score measured |
