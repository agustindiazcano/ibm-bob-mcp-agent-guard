"""Per-lane write-guard layer over watson_agent/tools.py's existing tools
(Phase 18 S3).

watson_agent/tools.py itself is never modified here -- narrowing its guard
by wrapping keeps AGENTS.md Section 8's "ask before changing the write
guard" rule intact; this only adds a stricter layer on top. A lane's
writer gets read_source_file, a write_test_file narrowed to its one owned
file, and run_tests; its critic gets read_source_file + run_tests and no
write tool at all.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from ..watson_agent.tools import (
    TOOL_SCHEMAS,
    SourceEditRejected,
    read_source_file,
    run_tests,
    write_test_file,
)

ToolSchemas = list[dict]
ToolRegistry = dict[str, Callable[..., dict]]

_SCHEMA_BY_NAME = {schema["function"]["name"]: schema for schema in TOOL_SCHEMAS}


def _schemas_for(*names: str) -> ToolSchemas:
    return [_SCHEMA_BY_NAME[name] for name in names]


def writer_toolset(sandbox: str | Path, owned: str) -> tuple[ToolSchemas, ToolRegistry]:
    """(schemas, registry) for one lane's writer stage.

    read_source_file and run_tests are the unmodified tools, rooted at
    whatever repo_path the caller passes at call time (expected to be
    `sandbox`). write_test_file additionally requires the write target to
    resolve to exactly `owned` -- the one file this lane may touch -- else
    raises SourceEditRejected naming the owned path, before ever reaching
    the real write_test_file (a second guard layer, not a replacement for
    its own tests/-only check).

    owned: path relative to `sandbox`, e.g. "tests/test_cart.py".
    """
    owned_resolved = (Path(sandbox) / owned).resolve()

    def _owned_write_test_file(repo_path: str, file_path: str, content: str) -> dict:
        target = (Path(repo_path) / file_path).resolve()
        if target != owned_resolved:
            raise SourceEditRejected(f"refused to write {file_path}: this lane may only write {owned}")
        return write_test_file(repo_path, file_path, content)

    schemas = _schemas_for("read_source_file", "write_test_file", "run_tests")
    registry: ToolRegistry = {
        "read_source_file": read_source_file,
        "write_test_file": _owned_write_test_file,
        "run_tests": run_tests,
    }
    return schemas, registry


def critic_toolset() -> tuple[ToolSchemas, ToolRegistry]:
    """(schemas, registry) for a lane's critic: read-only, no write tool."""
    schemas = _schemas_for("read_source_file", "run_tests")
    registry: ToolRegistry = {"read_source_file": read_source_file, "run_tests": run_tests}
    return schemas, registry
