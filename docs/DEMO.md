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

## Step 4 — Start the MCP server and let Bob fix it

```bash
repoguard mcp
```

In Bob, switch to the **RepoGuard Orchestrator** mode and say:

```
Analyse demo-repo and bring coverage above 80%.
```

Bob will:
1. Call `tool_find_gaps` to see what is missing
2. Activate the `pytest-conventions` skill
3. Write targeted tests for each gap (Fixer sub-agent)
4. Re-run `tool_full_pipeline` to confirm the gate passes
5. Write the evidence report to `bob-evidence/`

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
