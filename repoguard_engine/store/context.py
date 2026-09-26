"""Where and on what a run was measured: git commit/branch/dirty state and
the tool/runtime versions, with CI environment overrides."""

from __future__ import annotations

import os
import platform
import subprocess
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

_GIT_TIMEOUT = 10


@dataclass
class RunContext:
    commit_sha: str | None
    branch: str | None
    dirty: bool
    repository: str | None
    python_version: str
    engine_version: str


def _git(repo: Path, *args: str) -> str | None:
    """Run a read-only git command in repo; None if git is missing or the
    directory isn't inside a work tree."""
    try:
        proc = subprocess.run(
            ["git", *args], cwd=repo, capture_output=True, text=True, timeout=_GIT_TIMEOUT
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def engine_version() -> str:
    try:
        return metadata.version("repoguard")
    except metadata.PackageNotFoundError:
        return "0+unknown"


def collect_context(repo_path: str | Path) -> RunContext:
    """Git metadata for repo_path. GITHUB_SHA / GITHUB_REF_NAME /
    GITHUB_REPOSITORY override git (CI checkouts are often detached).
    `dirty` is scoped to repo_path itself (`git status --porcelain -- .`),
    so a target that's a subfolder of a bigger repo isn't marked dirty by
    unrelated changes elsewhere. Not a git work tree -> sha/branch None,
    dirty False."""
    repo = Path(repo_path).resolve()
    commit = os.environ.get("GITHUB_SHA") or _git(repo, "rev-parse", "HEAD")
    branch = os.environ.get("GITHUB_REF_NAME") or _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    status = _git(repo, "status", "--porcelain", "--", ".")
    return RunContext(
        commit_sha=commit,
        branch=branch,
        dirty=bool(status),
        repository=os.environ.get("GITHUB_REPOSITORY"),
        python_version=platform.python_version(),
        engine_version=engine_version(),
    )


def resolve_project_slug(repo_path: str | Path, explicit: str | None = None) -> str:
    """Project slug for a direct-DB write: --project > REPOGUARD_PROJECT >
    GITHUB_REPOSITORY > the repo directory's name."""
    return (
        explicit
        or os.environ.get("REPOGUARD_PROJECT")
        or os.environ.get("GITHUB_REPOSITORY")
        or Path(repo_path).resolve().name
    )
