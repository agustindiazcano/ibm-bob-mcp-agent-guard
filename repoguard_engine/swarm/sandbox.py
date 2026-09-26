"""Per-lane sandbox isolation for the swarm fix loop (Phase 18 S3).

Each lane gets its own throwaway copy of the target repo so parallel lanes
never race on the same tests/ or source files. The sandbox always lives in
the OS temp directory, never inside the target repo, so a write guard that
resolves a lane's path can't accidentally land back in the real repo.
"""

from __future__ import annotations

import shutil
import stat
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .._common import COPY_IGNORE

_IMPORT_PROBE_TIMEOUT = 30


class SandboxLeak(RuntimeError):
    """A lane sandbox couldn't be proven isolated from the real repo: either
    it's still on disk after cleanup, or code run inside it imported a
    package from outside it."""


def _onerror_clear_readonly(func, path, exc_info) -> None:
    """shutil.rmtree onerror handler: git/pytest leave read-only files
    (packed refs, some pycache under Windows) that a plain rmtree can't
    delete. Clear the read-only bit and retry once; if that still fails,
    let the exception surface -- the caller's own exists() check after
    cleanup is what turns a real failure into a reported SandboxLeak
    instead of a silently swallowed one."""
    Path(path).chmod(stat.S_IWRITE)
    func(path)


@contextmanager
def lane_sandbox(repo: str | Path, lane_id: str) -> Iterator[Path]:
    """Copy *repo* into a fresh temp directory for one lane and delete it
    afterward, even if the lane body raises. Yields the sandbox's copy of
    the repo root.

    Raises SandboxLeak if:
    - a real import from inside the sandbox resolves outside it (an
      editable install of the target package would otherwise let sandboxed
      code import the *original* source on sys.path instead of the copy --
      checked once, right after the copy, before the lane runs at all), or
    - the sandbox is still on disk after cleanup.
    """
    original = Path(repo).resolve()
    tmp = Path(tempfile.mkdtemp(prefix=f"repoguard_lane_{lane_id}_"))
    work = tmp / original.name
    try:
        shutil.copytree(original, work, ignore=COPY_IGNORE)
        _check_import_isolation(work)
        yield work
    finally:
        shutil.rmtree(tmp, ignore_errors=False, onerror=_onerror_clear_readonly)
        if tmp.exists():
            raise SandboxLeak(f"lane {lane_id} sandbox still exists after cleanup: {tmp}")


def _check_import_isolation(work: Path) -> None:
    """Import probe: run a subprocess with *work* as cwd and confirm the
    package it imports resolves inside the sandbox, not the real repo."""
    package = _top_level_package(work)
    if package is None:
        return  # nothing package-shaped at the repo root -- not a leak, just not this shape
    proc = subprocess.run(
        [sys.executable, "-c", f"import {package}; print({package}.__file__)"],
        cwd=work,
        capture_output=True,
        text=True,
        timeout=_IMPORT_PROBE_TIMEOUT,
    )
    if proc.returncode != 0:
        return  # the probe import itself failed -- a real bug in the target, not a sandbox leak
    resolved = Path(proc.stdout.strip()).resolve()
    if not resolved.is_relative_to(work):
        raise SandboxLeak(
            f"import {package} resolved to {resolved}, outside the sandbox {work} -- "
            "an editable install is shadowing the sandbox copy"
        )


def _top_level_package(work: Path) -> str | None:
    """Best-effort: the first directory directly under *work* with an
    __init__.py, i.e. the package the lane is meant to be testing."""
    for child in sorted(work.iterdir()):
        if child.is_dir() and (child / "__init__.py").is_file():
            return child.name
    return None
