"""
scripts/eval_fixloop.py -- Phase 19 E2: real fix-loop benchmark.

    python scripts/eval_fixloop.py --matrix eval/matrix.json --repeats 3 --out repoguard-out/eval/<timestamp>/

Replaces Phase 16's deferred benchmark_models.py. For each (provider,
model_id) x fixture pair in the matrix, runs the real AI fix loop
`--repeats` times on a fresh temp copy of the fixture, reads each run's
`repoguard-out/fix_run.json` (O1) and reports, per pair:

    ΔMS, gap closure, validity, integrity violations, success rate (k of K),
    and cost (wall time, LLM calls, tool calls) -- as min/median/max across
    repeats. K is small (3 by default), so we never report mean +/- sigma
    (docs/EVAL_GUARDRAILS_PLAN.md Section 6.3).

Human-gated: needs real credentials for each provider in the matrix. A
provider with no credentials configured is skipped (reported as SKIP, not a
failure) for every fixture in the matrix, so a partial credential set still
produces a partial report instead of an all-or-nothing run.

publish is always False here: this measures the fix loop, it never opens a
PR (AGENTS.md Section 4 -- the AI never writes outside tests/ regardless).
"""
from __future__ import annotations

import argparse
import json
import shutil
import statistics
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from repoguard_engine.ai_providers import AIProviderError, get_provider
from repoguard_engine.core import COPY_IGNORE
from repoguard_engine.watson_agent.orchestrator import run_fix_loop


def _copy_fixture(fixture_path: str) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="repoguard-eval-"))
    dest = tmp / Path(fixture_path).name
    shutil.copytree(fixture_path, dest, ignore=COPY_IGNORE)
    return dest


def _one_run(provider: str, model_id: str | None, fixture_path: str, gate_threshold: float) -> dict:
    """Fresh temp copy, one real fix-loop run, return its fix_run.json record."""
    repo = _copy_fixture(fixture_path)
    try:
        run_fix_loop(str(repo), provider=provider, model_id=model_id, gate_threshold=gate_threshold, publish=False)
        fix_run_path = repo / "repoguard-out" / "fix_run.json"
        return json.loads(fix_run_path.read_text(encoding="utf-8")) if fix_run_path.exists() else {}
    finally:
        shutil.rmtree(repo.parent, ignore_errors=True)


def _metrics(record: dict, ceiling: int | None) -> dict:
    before = record.get("before") or {}
    after = record.get("after") or {}
    k_b, n, k_a = before.get("killed"), before.get("total"), after.get("killed") if after else None

    delta_ms = gap_closure = None
    if k_b is not None and k_a is not None and n:
        delta_ms = round(100 * (k_a - k_b) / n, 2)
        if ceiling is not None and ceiling > k_b:
            gap_closure = round((k_a - k_b) / (ceiling - k_b), 3)

    acceptance = record.get("acceptance") or []
    validity = round(sum(1 for a in acceptance if a.get("accepted")) / len(acceptance), 3) if acceptance else None

    integrity = record.get("integrity") or {}
    integrity_violations = sum(v for v in integrity.values() if isinstance(v, int))

    success = (
        record.get("status") == "accepted"
        and integrity_violations == 0
        and k_a is not None and k_b is not None and k_a > k_b
    )
    return {
        "delta_ms": delta_ms,
        "gap_closure": gap_closure,
        "validity": validity,
        "integrity_violations": integrity_violations,
        "success": success,
        "wall_s_total": (record.get("wall_s") or {}).get("total"),
        "llm_calls": record.get("llm_calls"),
        "tool_calls": len(record.get("tool_calls") or []),
    }


def _summary(values: list) -> dict:
    clean = [v for v in values if v is not None]
    if not clean:
        return {"min": None, "median": None, "max": None}
    return {"min": min(clean), "median": statistics.median(clean), "max": max(clean)}


def run_matrix(matrix: dict, repeats: int, out_dir: Path) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    gate_threshold = matrix.get("gate_threshold", 80.0)
    rows: list[dict] = []

    for combo in matrix["providers"]:
        provider, model_id = combo["provider"], combo.get("model_id")
        label = f"{provider}/{model_id or 'default'}"
        try:
            get_provider(provider=provider, model_id=model_id)
        except AIProviderError as exc:
            for fixture in matrix["fixtures"]:
                print(f"SKIP {label} x {fixture['name']}: {exc}")
            continue

        for fixture in matrix["fixtures"]:
            runs = []
            for i in range(repeats):
                print(f"=== {label} x {fixture['name']}, repeat {i + 1}/{repeats} ===")
                record = _one_run(provider, model_id, fixture["path"], gate_threshold)
                metrics = _metrics(record, fixture.get("ceiling"))
                runs.append(metrics)
                run_path = out_dir / f"{provider}_{fixture['name']}_{i}.json"
                run_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

            rows.append({
                "provider": provider,
                "model_id": model_id,
                "fixture": fixture["name"],
                "repeats": repeats,
                "success_k_of_n": sum(1 for r in runs if r["success"]),
                "delta_ms": _summary([r["delta_ms"] for r in runs]),
                "gap_closure": _summary([r["gap_closure"] for r in runs]),
                "validity": _summary([r["validity"] for r in runs]),
                "integrity_violations": _summary([r["integrity_violations"] for r in runs]),
                "wall_s_total": _summary([r["wall_s_total"] for r in runs]),
            })

    (out_dir / "eval.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return rows


def print_table(rows: list[dict]) -> None:
    if not rows:
        print("\n(no rows -- every provider in the matrix was skipped, see SKIP lines above)")
        return
    print("\n| Provider/model | Fixture | k/K | ΔMS min/med/max | Gap closure | Validity | Integrity viol. | Wall s |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        label = f"{r['provider']}/{r['model_id'] or 'default'}"
        d, g, v, iv, w = r["delta_ms"], r["gap_closure"], r["validity"], r["integrity_violations"], r["wall_s_total"]
        print(
            f"| {label} | {r['fixture']} | {r['success_k_of_n']}/{r['repeats']} "
            f"| {d['min']}/{d['median']}/{d['max']} | {g['min']}/{g['median']}/{g['max']} "
            f"| {v['min']}/{v['median']}/{v['max']} | {iv['min']}/{iv['median']}/{iv['max']} "
            f"| {w['min']}/{w['median']}/{w['max']} |"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--matrix", required=True, help="Path to a matrix JSON file (see eval/matrix.json)")
    parser.add_argument("--repeats", type=int, default=3, help="K repetitions per (provider, fixture) pair")
    parser.add_argument("--out", default=None, help="Output dir (default: repoguard-out/eval/<UTC timestamp>/)")
    args = parser.parse_args()

    matrix = json.loads(Path(args.matrix).read_text(encoding="utf-8"))
    out_dir = Path(args.out) if args.out else Path("repoguard-out/eval") / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    rows = run_matrix(matrix, args.repeats, out_dir)
    print_table(rows)
    print(f"\nWrote {out_dir / 'eval.json'}")


if __name__ == "__main__":
    main()
