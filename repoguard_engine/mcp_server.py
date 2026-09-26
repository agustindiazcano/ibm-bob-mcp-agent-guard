"""MCP server exposing 9 RepoGuard tools via FastMCP."""

from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP

from .pipeline import run_pipeline
from .core import measure_coverage, find_coverage_gaps, run_mutation, compute_risk
from .api_check import find_untested_endpoints, run_endpoint_smoke_tests
from .visual import capture_screenshot, pixel_diff, check_accessibility
from .narrative import generate_summary

mcp_app = FastMCP("repoguard")


# ---------------------------------------------------------------------------
# Tool 1 — measure_coverage
# ---------------------------------------------------------------------------
@mcp_app.tool()
def tool_measure_coverage(repo_path: str, detail: bool = False) -> dict:
    """
    Run pytest with coverage on the given repository and return coverage metrics.

    Args:
        repo_path: Absolute or relative path to the target repository root.
        detail: If True, include missing_lines_by_file in the response.

    Returns:
        Compact: percent, covered_lines, total_lines.
        Full (detail=True): + missing_lines_by_file.
    """
    result = measure_coverage(repo_path)
    compact = {
        "percent": result.percent,
        "covered_lines": result.covered_lines,
        "total_lines": result.total_lines,
    }
    if not detail:
        return compact
    return {**compact, "missing_lines_by_file": result.missing_lines}


# ---------------------------------------------------------------------------
# Tool 2 — find_gaps
# ---------------------------------------------------------------------------
@mcp_app.tool()
def tool_find_gaps(repo_path: str, detail: bool = False) -> dict:
    """
    Measure coverage and return a structured gap report.

    Args:
        repo_path: Path to the target repository root.
        detail: If True, include missing_lines_by_file in the response.

    Returns:
        Compact: coverage_percent, uncovered_file_count, uncovered_files.
        Full (detail=True): + missing_lines_by_file.
    """
    coverage = measure_coverage(repo_path)
    gap = find_coverage_gaps(coverage, repo_path=repo_path)
    compact = {
        "coverage_percent": coverage.percent,
        "uncovered_file_count": len(gap.uncovered_files),
        "uncovered_files": gap.uncovered_files,
    }
    if not detail:
        return compact
    return {**compact, "missing_lines_by_file": gap.missing_lines_by_file}


# ---------------------------------------------------------------------------
# Tool 3 — run_mutation_analysis
# ---------------------------------------------------------------------------
@mcp_app.tool()
def tool_run_mutation(
    repo_path: str,
    paths_to_mutate: str = ".",
    tests_dir: str = "tests",
    detail: bool = False,
) -> dict:
    """
    Run mutation testing on the target repo and return the mutation score.

    Args:
        repo_path: Path to the target repository root.
        paths_to_mutate: Subdirectory or file to mutate (default: ".").
        tests_dir: Test directory (default: "tests").
        detail: If True, include surviving_mutant_ids in the response.

    Returns:
        Compact: score, killed, survived, total.
        Full (detail=True): + surviving_mutant_ids.
    """
    result = run_mutation(repo_path, paths_to_mutate=paths_to_mutate, tests_dir=tests_dir)
    compact = {
        "score": result.score,
        "killed": result.killed,
        "survived": result.survived,
        "total": result.total,
    }
    if not detail:
        return compact
    return {**compact, "surviving_mutant_ids": result.surviving_mutant_ids}


# ---------------------------------------------------------------------------
# Tool 4 — find_untested_endpoints
# ---------------------------------------------------------------------------
@mcp_app.tool()
def tool_find_untested_endpoints(repo_path: str, detail: bool = False) -> dict:
    """
    Detect FastAPI route-decorated functions that have no corresponding test.

    Args:
        repo_path: Path to the target repository root.
        detail: If True, include full endpoint details (file, function, method).

    Returns:
        Compact: untested_count, untested_paths.
        Full (detail=True): + list of dicts with file, function, method, path.
    """
    endpoints = find_untested_endpoints(repo_path)
    untested = [ep for ep in endpoints if not ep.has_test]
    compact = {
        "untested_count": len(untested),
        "untested_paths": [f"{ep.method} {ep.path}" for ep in untested],
    }
    if not detail:
        return compact
    return {
        **compact,
        "untested_endpoints": [
            {"file": ep.file, "function": ep.function, "method": ep.method, "path": ep.path}
            for ep in untested
        ],
    }


# ---------------------------------------------------------------------------
# Tool 5 — smoke_test_endpoints
# ---------------------------------------------------------------------------
@mcp_app.tool()
def tool_smoke_test_endpoints(base_url: str, repo_path: str, detail: bool = False) -> dict:
    """
    Fire a minimal HTTP request at each detected endpoint and return status codes.

    Args:
        base_url: Running server base URL, e.g. "http://localhost:8000".
        repo_path: Path to the target repository root (for endpoint detection).
        detail: If True, include all endpoint results; otherwise only failures.

    Returns:
        Compact: ok_count, fail_count, failures (only failed endpoints).
        Full (detail=True): + all_results map.
    """
    endpoints = find_untested_endpoints(repo_path)
    all_results: dict = run_endpoint_smoke_tests(base_url, endpoints)
    failures = {k: v for k, v in all_results.items() if not v.get("ok", True)}
    compact = {
        "ok_count": sum(1 for v in all_results.values() if v.get("ok", True)),
        "fail_count": len(failures),
        "failures": failures,
    }
    if not detail:
        return compact
    return {**compact, "all_results": all_results}


# ---------------------------------------------------------------------------
# Tool 6 — full_pipeline
# ---------------------------------------------------------------------------
@mcp_app.tool()
def tool_full_pipeline(
    repo_path: str,
    include_mutation: bool = False,
    gate_threshold: float = 80.0,
    detail: bool = False,
) -> dict:
    """
    Run the full RepoGuard pipeline: coverage → gaps → risk → gate.

    Args:
        repo_path: Path to the target repository root.
        include_mutation: Whether to run mutation testing (slow).
        gate_threshold: Minimum coverage % to pass the gate.
        detail: If True, return full dashboard dict; otherwise key metrics only.

    Returns:
        Compact: coverage_percent, mutation_score, gap_count, passed_gate.
        Full (detail=True): full dashboard dict + passed_gate.
    """
    result = run_pipeline(
        repo_path,
        include_mutation=include_mutation,
        gate_threshold=gate_threshold,
    )
    compact = {
        "coverage_percent": result.dashboard.get("coverage", {}).get("percent"),
        "mutation_score": result.dashboard.get("mutation", {}).get("score") if result.dashboard.get("mutation") else None,
        "gap_count": len(result.dashboard.get("gaps", {}).get("uncovered_files", [])),
        "passed_gate": result.passed_gate,
    }
    if not detail:
        return compact
    return {**result.dashboard, "passed_gate": result.passed_gate}


# ---------------------------------------------------------------------------
# Tool 7 — capture_screenshot
# ---------------------------------------------------------------------------
@mcp_app.tool()
def tool_capture_screenshot(url: str, output_path: str, detail: bool = False) -> dict:
    """
    Capture a screenshot of a URL and save it to output_path.

    Args:
        url: URL to screenshot.
        output_path: File path to save the PNG.
        detail: If True, include width, height, and error in the response.

    Returns:
        Compact: ok, path.
        Full (detail=True): + width, height, error.
    """
    result = capture_screenshot(url, output_path)
    compact = {
        "ok": result.ok,
        "path": result.path,
    }
    if not detail:
        return compact
    return {
        **compact,
        "width": result.width,
        "height": result.height,
        "error": result.error,
    }


# ---------------------------------------------------------------------------
# Tool 8 — check_accessibility
# ---------------------------------------------------------------------------
@mcp_app.tool()
def tool_check_accessibility(url: str, detail: bool = False) -> dict:
    """
    Run axe-core accessibility checks on a URL.

    Args:
        url: URL to check.
        detail: If True, include passes and incomplete counts.

    Returns:
        Compact: ok, violation_count, violations. ok=False means the check
            could not run at all (e.g. axe-playwright-python not installed) —
            distinct from ok=True with violation_count=0 (a real clean pass).
        Full (detail=True): + passes, incomplete, error.
    """
    result = check_accessibility(url)
    compact = {
        "ok": result.ok,
        "violation_count": len(result.violations),
        "violations": result.violations,
    }
    if not detail:
        return compact
    return {
        **compact,
        "passes": result.passes,
        "incomplete": result.incomplete,
        "error": result.error,
    }


# ---------------------------------------------------------------------------
# Tool 9 — generate_summary
# ---------------------------------------------------------------------------
@mcp_app.tool()
def tool_generate_summary(repo_path: str, detail: bool = False) -> dict:
    """
    Measure repo_path (coverage, gaps, risk) and ask the configured AI
    provider (Vertex AI by default, or watsonx.ai) for a short plain-English
    summary of those exact numbers. Advisory text only — never a source of
    any metric; every number the summary can mention was already measured by
    the engine before this tool ever calls the AI provider.

    Requires credentials for the selected provider (see docs/WATSONX_SETUP.md
    / docs/VERTEX_SETUP.md).
    ok=False means the summary could not be generated (missing credentials,
    SDK not installed, or an API error) — the measured numbers themselves are
    unaffected either way; call tool_full_pipeline for those.

    Args:
        repo_path: Path to the target repository root.
        detail: If True, include the full error string on failure.

    Returns:
        Compact: ok, summary.
        Full (detail=True): + error.
    """
    result = run_pipeline(repo_path)
    narrative = generate_summary(result.dashboard)
    compact = {
        "ok": narrative.ok,
        "summary": narrative.text,
    }
    if not detail:
        return compact
    return {**compact, "error": narrative.error}
