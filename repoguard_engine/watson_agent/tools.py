"""Tool schemas + implementations the watsonx.ai orchestrator can call.

Only write_test_file can write anything, and it hard-rejects any path that
doesn't resolve under <repo_path>/tests/. This is the real replacement for
.bob/hooks/safety-guard.mjs's external Node.js intercept plus the
01-tests-only.md prose rule: enforcement now lives in the tool itself, so it
can't be skipped by a model that ignores its system prompt (AGENTS.md Section
4: "Agents that write tests may only edit tests/").

Calls pipeline/core/api_check functions directly, in-process -- same
layering as web/server.py, no MCP round-trip needed since this orchestrator
and the engine live in the same process.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from ..api_check import find_untested_endpoints
from ..core import find_coverage_gaps, measure_coverage, run_mutation


class SourceEditRejected(PermissionError):
    """Raised when the model tries to read outside the repo or write outside tests/."""


def measure_coverage_tool(repo_path: str) -> dict:
    result = measure_coverage(repo_path)
    return {
        "percent": result.percent,
        "covered_lines": result.covered_lines,
        "total_lines": result.total_lines,
    }


def find_gaps_tool(repo_path: str) -> dict:
    coverage = measure_coverage(repo_path)
    gaps = find_coverage_gaps(coverage, repo_path=repo_path)
    return {
        "coverage_percent": coverage.percent,
        "uncovered_files": gaps.uncovered_files,
        "missing_lines_by_file": gaps.missing_lines_by_file,
    }


def run_mutation_tool(repo_path: str, paths_to_mutate: str = ".", tests_dir: str = "tests") -> dict:
    result = run_mutation(repo_path, paths_to_mutate=paths_to_mutate, tests_dir=tests_dir)
    return {
        "score": result.score,
        "killed": result.killed,
        "survived": result.survived,
        "total": result.total,
        "surviving_mutant_ids": result.surviving_mutant_ids,
    }


def find_untested_endpoints_tool(repo_path: str) -> dict:
    endpoints = find_untested_endpoints(repo_path)
    return {"untested_endpoints": [dataclasses.asdict(e) for e in endpoints]}


def read_source_file(repo_path: str, file_path: str) -> dict:
    """Read-only. Any path inside repo_path -- used for context before writing a test."""
    root = Path(repo_path).resolve()
    target = (root / file_path).resolve()
    if not target.is_relative_to(root):
        raise SourceEditRejected(f"refused to read {file_path}: escapes {repo_path}")
    return {"content": target.read_text(encoding="utf-8")}


def write_test_file(repo_path: str, file_path: str, content: str) -> dict:
    """
    The ONLY write tool given to the model. Hard-enforces that agents writing
    tests may only edit tests/ (AGENTS.md Section 4). Raises SourceEditRejected
    for any path that doesn't resolve under <repo_path>/tests/.
    """
    root = Path(repo_path).resolve()
    tests_root = root / "tests"
    target = (root / file_path).resolve()
    if not target.is_relative_to(tests_root):
        raise SourceEditRejected(
            f"refused to write {file_path}: only paths under tests/ are allowed"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"ok": True, "path": str(target.relative_to(root))}


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_source_file",
            "description": "Read a file's exact contents before writing a test for it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path relative to the repo root."},
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_test_file",
            "description": "Write or overwrite a pytest test file. Only paths under tests/ are accepted; any other path is rejected.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path relative to the repo root; must be under tests/.",
                    },
                    "content": {"type": "string", "description": "Full file content."},
                },
                "required": ["file_path", "content"],
            },
        },
    },
]

TOOL_REGISTRY = {
    "read_source_file": read_source_file,
    "write_test_file": write_test_file,
}
