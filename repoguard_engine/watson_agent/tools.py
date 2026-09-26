"""Tool schemas + implementations the watsonx.ai orchestrator can call.

Only write_test_file can write anything, and it hard-rejects any path that
doesn't resolve under <repo_path>/tests/. This is the real replacement for
.bob/hooks/safety-guard.mjs's external Node.js intercept plus the
01-tests-only.md prose rule: enforcement now lives in the tool itself, so it
can't be skipped by a model that ignores its system prompt (AGENTS.md Section
4: "Agents that write tests may only edit tests/").

run_tests executes pytest (real subprocess, sys.executable, never a bare
"pytest" -- AGENTS.md Section 9) but writes nothing; it's the anti-
hallucination grounding tool -- the model gets real pass/fail output instead
of guessing whether a test it just wrote actually runs against real source.
Added after a live Vertex/Gemini run twice produced a test file calling a
method that doesn't exist on the class under test (see PENDING.md Phase 11):
without this tool, the only way that surfaced was run_mutation()'s baseline
guard several minutes later, at the very end of the loop.

Calls pipeline/core/api_check functions directly, in-process -- same
layering as web/server.py, no MCP round-trip needed since this orchestrator
and the engine live in the same process.
"""

from __future__ import annotations

import dataclasses
import os
import subprocess
import sys
from pathlib import Path

from ..api_check import find_untested_endpoints
from ..core import find_coverage_gaps, measure_coverage, run_mutation

_RUN_TESTS_TIMEOUT = 60
_RUN_TESTS_OUTPUT_CHARS = 4000


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


def run_tests(repo_path: str, file_path: str = "tests") -> dict:
    """
    Anti-hallucination grounding tool: actually executes pytest against the
    unmutated source and returns the real exit code and output, instead of
    letting the model guess whether a test it just wrote actually passes.

    Read-only with respect to source and tests -- it runs code, it doesn't
    write any. Restricted to tests/ (like write_test_file) so the model can't
    use it to probe or execute anything outside its sandbox. Always
    sys.executable, never a bare "pytest" -- AGENTS.md Section 9's PATH
    pitfall applies here exactly as it does in core.py.
    """
    root = Path(repo_path).resolve()
    tests_root = root / "tests"
    target = (root / file_path).resolve()
    if not (target == tests_root or target.is_relative_to(tests_root)):
        raise SourceEditRejected(f"refused to run {file_path}: only tests/ (or a path under it) is allowed")

    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(target), "-q", "--no-header"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=_RUN_TESTS_TIMEOUT,
    )
    output = (proc.stdout + proc.stderr)[-_RUN_TESTS_OUTPUT_CHARS:]
    return {"exit_code": proc.returncode, "passed": proc.returncode == 0, "output": output}


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
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": (
                "Actually run pytest against a test file (or all of tests/) and see the real "
                "pass/fail result and output. Call this after write_test_file and before giving "
                "a final answer or verdict -- do not assume a test passes without running it. "
                "If it fails against the unmutated source, that means your test is wrong (a "
                "typo, a method that doesn't exist, wrong expected value) unless you have "
                "concrete evidence from read_source_file that the source itself is buggy."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path relative to the repo root, under tests/. Omit to run the whole tests/ directory.",
                    },
                },
                "required": [],
            },
        },
    },
]

TOOL_REGISTRY = {
    "read_source_file": read_source_file,
    "write_test_file": write_test_file,
    "run_tests": run_tests,
}
