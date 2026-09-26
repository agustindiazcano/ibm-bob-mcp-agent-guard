"""Small helpers shared by the measurement modules (core.py, mutation.py).

Kept separate so mutation.py can live in its own file without importing
core.py (which re-exports mutation's public names).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

# Directories never copied into a mutant copy, a lane sandbox or an Autofix
# sandbox: caches, this tool's own outputs, and VCS metadata. Copying them
# is at best wasted I/O and at worst stale bytecode leaking into a
# measurement (AGENTS.md Section 9).
COPY_IGNORE = shutil.ignore_patterns("__pycache__", ".pytest_cache", "repoguard-out", "watson-evidence", ".git")


def require_repo_dir(repo_path: str | Path) -> Path:
    """
    Validate repo_path up front, with a message a caller can act on.

    Without this, a bad path reaches subprocess.run(cwd=repo, ...) instead
    and raises a raw OS-level error (NotADirectoryError: [WinError 267] The
    directory name is invalid, or FileNotFoundError on Linux) -- accurate,
    but useless to whoever's holding a typo'd path, and on web/server.py's
    /api/analyze it surfaced as an unhandled 500 instead of a 400 with a
    clear reason.
    """
    repo = Path(repo_path)
    if not repo.is_dir():
        raise NotADirectoryError(f"repo_path does not exist or is not a directory: {repo_path}")
    return repo


def write_out(repo_path: Path, name: str, data: object) -> None:
    """Write *data* as JSON to <repo_path>/repoguard-out/<name>.json."""
    out_dir = repo_path / "repoguard-out"
    out_dir.mkdir(exist_ok=True)
    (out_dir / f"{name}.json").write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
