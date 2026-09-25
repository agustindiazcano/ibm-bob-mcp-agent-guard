"""MCP server exposing 8 RepoGuard tools via FastMCP."""

from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP

from .pipeline import run_pipeline
from .core import measure_coverage, find_coverage_gaps, run_mutation, compute_risk
from .api_check import find_untested_endpoints, run_endpoint_smoke_tests
from .visual import capture_screenshot, pixel_diff, check_accessibility

mcp_app = FastMCP("repoguard")


# ---------------------------------------------------------------------------
# Tool 1 — measure_coverage
# ---------------------------------------------------------------------------
@mcp_app.tool()
def tool_measure_coverage(repo_path: str) -> dict:
    """
    Run pytest with coverage on the given repository and return coverage metrics.

    Args:
        repo_path: Absolute or relative path to the target repository root.

    Returns:
        Dict with percent, covered_lines, total_lines, and missing_lines_by_file.
    """
    result = measure_coverage(repo_path)
    return {
        "percent": result.percent,
        "covered_lines": result.covered_lines,
        "total_lines": result.total_lines,
        "missing_lines_by_file": result.missing_lines,
    }


# ---------------------------------------------------------------------------
# Tool 2 — find_gaps
# ---------------------------------------------------------------------------
@mcp_app.tool()
def tool_find_gaps(repo_path: str) -> dict:
    """
    Measure coverage and return a structured gap report.

    Args:
        repo_path: Path to the target repository root.

    Returns:
        Dict with uncovered_files and missing_lines_by_file.
    """
    coverage = measure_coverage(repo_path)
    gap = find_coverage_gaps(coverage)
    return {
        "coverage_percent": coverage.percent,
        "uncovered_files": gap.uncovered_files,
        "missing_lines_by_file": gap.missing_lines_by_file,
    }


# ---------------------------------------------------------------------------
# Tool 3 — run_mutation_analysis
# ---------------------------------------------------------------------------
@mcp_app.tool()
def tool_run_mutation(repo_path: str, paths_to_mutate: str = ".", tests_dir: str = "tests") -> dict:
    """
    Run mutation testing on the target repo and return the mutation score.

    Args:
        repo_path: Path to the target repository root.
        paths_to_mutate: Subdirectory or file to mutate (default: ".").
        tests_dir: Test directory (default: "tests").

    Returns:
        Dict with score, killed, survived, total.
    """
    result = run_mutation(repo_path, paths_to_mutate=paths_to_mutate, tests_dir=tests_dir)
    return {
        "score": result.score,
        "killed": result.killed,
        "survived": result.survived,
        "total": result.total,
    }


# ---------------------------------------------------------------------------
# Tool 4 — find_untested_endpoints
# ---------------------------------------------------------------------------
@mcp_app.tool()
def tool_find_untested_endpoints(repo_path: str) -> list[dict]:
    """
    Detect FastAPI route-decorated functions that have no corresponding test.

    Args:
        repo_path: Path to the target repository root.

    Returns:
        List of dicts with file, function, method, path, has_test.
    """
    endpoints = find_untested_endpoints(repo_path)
    return [
        {
            "file": ep.file,
            "function": ep.function,
            "method": ep.method,
            "path": ep.path,
            "has_test": ep.has_test,
        }
        for ep in endpoints
        if not ep.has_test
    ]


# ---------------------------------------------------------------------------
# Tool 5 — smoke_test_endpoints
# ---------------------------------------------------------------------------
@mcp_app.tool()
def tool_smoke_test_endpoints(base_url: str, repo_path: str) -> dict:
    """
    Fire a minimal HTTP request at each detected endpoint and return status codes.

    Args:
        base_url: Running server base URL, e.g. "http://localhost:8000".
        repo_path: Path to the target repository root (for endpoint detection).

    Returns:
        Dict mapping "METHOD /path" to {"status_code": int, "ok": bool}.
    """
    endpoints = find_untested_endpoints(repo_path)
    return run_endpoint_smoke_tests(base_url, endpoints)


# ---------------------------------------------------------------------------
# Tool 6 — full_pipeline
# ---------------------------------------------------------------------------
@mcp_app.tool()
def tool_full_pipeline(
    repo_path: str,
    include_mutation: bool = False,
    gate_threshold: float = 80.0,
) -> dict:
    """
    Run the full RepoGuard pipeline: coverage → gaps → risk → gate.

    Args:
        repo_path: Path to the target repository root.
        include_mutation: Whether to run mutation testing (slow).
        gate_threshold: Minimum coverage % to pass the gate.

    Returns:
        Full dashboard dict plus passed_gate boolean.
    """
    result = run_pipeline(
        repo_path,
        include_mutation=include_mutation,
        gate_threshold=gate_threshold,
    )
    return {**result.dashboard, "passed_gate": result.passed_gate}


# ---------------------------------------------------------------------------
# Tool 7 — capture_screenshot
# ---------------------------------------------------------------------------
@mcp_app.tool()
def tool_capture_screenshot(url: str, output_path: str) -> dict:
    """
    Capture a screenshot of a URL and save it to output_path.

    Args:
        url: URL to screenshot.
        output_path: File path to save the PNG.

    Returns:
        Dict with path, width, height, ok, error.
    """
    result = capture_screenshot(url, output_path)
    return {
        "path": result.path,
        "width": result.width,
        "height": result.height,
        "ok": result.ok,
        "error": result.error,
    }


# ---------------------------------------------------------------------------
# Tool 8 — check_accessibility
# ---------------------------------------------------------------------------
@mcp_app.tool()
def tool_check_accessibility(url: str) -> dict:
    """
    Run axe-core accessibility checks on a URL.

    Args:
        url: URL to check.

    Returns:
        Dict with violations list, passes count, incomplete count.
    """
    result = check_accessibility(url)
    return {
        "violations": result.violations,
        "violation_count": len(result.violations),
        "passes": result.passes,
        "incomplete": result.incomplete,
    }
