"""Where and with what a run was measured: project slug, git state, versions.

No SQLAlchemy import. Git is optional: outside a git checkout (or on an image
without git, like Cloud Run's) the git fields are None -- unknown, not guessed.
"""

from __future__ import annotations

import os
import platform
import re
import subprocess
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

from ..core import MUTATION_OPERATORS_HASH
from . import StoreError

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,99}$")

# Files the engine and the fix loop themselves leave in a target repo. They
# don't change what is measured, so they don't make a working tree "dirty";
# otherwise every run after the first in a repo that doesn't gitignore them
# would be recorded as dirty and drop out of the history views.
_ARTIFACT_DIRS = {"repoguard-out", "watson-evidence", "__pycache__", ".pytest_cache"}


@dataclass
class RunContext:
    project: str
    repo_url: str | None
    commit_sha: str | None
    branch: str | None
    dirty: bool | None
    engine_version: str
    operators_hash: str
    python_version: str


def collect_context(repo_path: str | Path, project: str | None = None) -> RunContext:
    """Describe the checkout at *repo_path* before it is measured. Writes nothing."""
    repo = Path(repo_path)
    sha = _git(repo, "rev-parse", "HEAD")
    branch = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    if branch == "HEAD":  # detached, e.g. actions/checkout on a pull request
        branch = None
    github_repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com").strip()
    return RunContext(
        project=resolve_project_slug(repo, project),
        repo_url=f"{server}/{github_repo}" if github_repo else None,
        # git's own answer first: GITHUB_* describe the workflow's repo, which
        # isn't necessarily the directory being measured.
        commit_sha=sha or os.environ.get("GITHUB_SHA") or None,
        branch=branch or os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME") or None,
        dirty=_is_dirty(repo),
        engine_version=_engine_version(),
        operators_hash=MUTATION_OPERATORS_HASH,
        python_version=platform.python_version(),
    )


def resolve_project_slug(repo_path: str | Path, explicit: str | None = None) -> str:
    """Project slug precedence (DATA_PLATFORM.md §13, decision #3):
    --project > REPOGUARD_PROJECT > GITHUB_REPOSITORY > repo directory name.
    Explicit values must already be valid slugs; derived ones are slugified."""
    for label, value in (("--project", explicit), ("REPOGUARD_PROJECT", os.environ.get("REPOGUARD_PROJECT"))):
        if value and value.strip():
            slug = value.strip()
            if not _SLUG_RE.match(slug):
                raise StoreError(
                    f"invalid project slug from {label}: {slug!r} -- use 1-100 lowercase "
                    "letters, digits, '.', '_' or '-', starting with a letter or digit"
                )
            return slug
    github_repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    for value in (github_repo, Path(repo_path).resolve().name):
        slug = slugify(value)
        if slug:
            return slug
    raise StoreError(f"could not derive a project slug for {repo_path}; pass --project")


def slugify(value: str) -> str:
    """'Owner/My Repo' -> 'owner-my-repo'."""
    slug = re.sub(r"[^a-z0-9._-]+", "-", value.lower()).strip("-._")
    return slug[:100]


def _git(repo: Path, *args: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", *args], cwd=repo, capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    out = proc.stdout.strip()
    return out if proc.returncode == 0 and out else None


def _is_dirty(repo: Path) -> bool | None:
    """True if anything under *repo* differs from HEAD (tracked changes or
    untracked files), ignoring the tool artifacts above. None if unknown."""
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain", "-z", "--", "."],
            cwd=repo, capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    entries = proc.stdout.split("\0")
    i = 0
    while i < len(entries):
        entry = entries[i]
        i += 1
        if not entry:
            continue
        status, path = entry[:2], entry[3:]
        if status[0] in "RC":
            i += 1  # -z puts a rename's original path in the next field
        if not _is_artifact(path):
            return True
    return False


def _is_artifact(path: str) -> bool:
    parts = [p for p in path.split("/") if p]
    name = parts[-1] if parts else ""
    return (
        any(p in _ARTIFACT_DIRS for p in parts)
        or name.endswith(".pyc")
        # coverage data files, but not .coveragerc -- that one changes what's measured
        or name == ".coverage"
        or name.startswith(".coverage.")
    )


def _engine_version() -> str:
    try:
        return metadata.version("repoguard")
    except metadata.PackageNotFoundError:
        return "unknown"  # running from a source tree that was never pip-installed
