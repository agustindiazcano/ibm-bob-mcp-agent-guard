"""
Phase 18 checks for scripts/verify.py (multi-agent swarm groundwork).

    phase18-s3 — lane sandbox + owned-path write guard (Step S3): an owned
                 write succeeds; every other path (a source file, another
                 lane's file, tests/conftest.py, a ".." escape, an absolute
                 path into the real repo's tests/) raises SourceEditRejected;
                 the critic toolset has no write tool at all; the sandbox is
                 gone after both a normal exit and an exception inside the
                 context manager; the real demo-repo is byte-for-byte
                 unchanged throughout.

Each check runs its script in a fresh interpreter (sys.executable), same as
verify.py and verify_phase17.py.
"""

from __future__ import annotations

import subprocess
import sys


def _run_script(script: str, timeout: int) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout + proc.stderr


_PHASE18_S3_SCRIPT = r"""
import hashlib
from pathlib import Path
from repoguard_engine.swarm.sandbox import lane_sandbox
from repoguard_engine.swarm.guard import writer_toolset, critic_toolset
from repoguard_engine.watson_agent.tools import SourceEditRejected

def file_hashes(root):
    out = {}
    for p in sorted(Path(root).rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and '.git' not in p.parts and 'repoguard-out' not in p.parts:
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out

real_repo = Path('demo-repo').resolve()
before = file_hashes(real_repo)
owned = 'tests/test_lane_probe.py'
sandbox_seen = None

with lane_sandbox(real_repo, 'lane-0') as sandbox:
    sandbox_seen = sandbox
    schemas, registry = writer_toolset(sandbox, owned)
    assert {s['function']['name'] for s in schemas} == {'read_source_file', 'write_test_file', 'run_tests'}

    write = registry['write_test_file']
    result = write(repo_path=str(sandbox), file_path=owned, content='def test_x():\n    assert True\n')
    assert result['ok'] is True, result
    print('OK: owned write succeeded')

    rejected = {}
    for bad_path in (
        'shop/cart.py',
        'tests/test_another_lane.py',
        'tests/conftest.py',
        'tests/../shop/cart.py',
        '../x.py',
    ):
        try:
            write(repo_path=str(sandbox), file_path=bad_path, content='x = 1\n')
            rejected[bad_path] = False
        except SourceEditRejected:
            rejected[bad_path] = True
    assert all(rejected.values()), rejected
    print(f'OK: {len(rejected)} out-of-scope paths all raised SourceEditRejected')

    real_target = str(real_repo / 'tests' / 'test_should_never_exist.py')
    try:
        write(repo_path=str(sandbox), file_path=real_target, content='x = 1\n')
        raise AssertionError('an absolute path into the real repo tests/ was accepted')
    except SourceEditRejected:
        pass
    assert not (real_repo / 'tests' / 'test_should_never_exist.py').exists()
    print('OK: absolute path into the real repo tests/ raised SourceEditRejected')

    c_schemas, c_registry = critic_toolset()
    assert {s['function']['name'] for s in c_schemas} == {'read_source_file', 'run_tests'}
    assert 'write_test_file' not in c_registry
    print('OK: critic toolset has no write tool')

assert not sandbox_seen.exists(), 'sandbox still exists after a normal exit'
print('OK: sandbox gone after normal exit')

leaked = None
try:
    with lane_sandbox(real_repo, 'lane-1') as sandbox2:
        leaked = sandbox2
        raise RuntimeError('boom')
except RuntimeError:
    pass
assert leaked is not None and not leaked.exists(), 'sandbox not cleaned up after an exception'
print('OK: sandbox gone after an exception inside the context manager')

after = file_hashes(real_repo)
assert before == after, 'the real demo-repo changed during the lane sandbox test'
print('OK: real demo-repo byte-for-byte unchanged throughout')
"""


def check_phase18_s3() -> bool:
    """Lane sandbox + owned-path write guard: owned write succeeds, every
    out-of-scope path (source, another lane's file, conftest.py, a ".."
    escape, an absolute path into the real repo) is rejected, the critic
    has no write tool, sandboxes are cleaned up on both a normal exit and
    an exception, and the real demo-repo never changes."""
    print("=== Phase 18 S3: lane sandbox + owned-path write guard ===")
    rc, out = _run_script(_PHASE18_S3_SCRIPT, timeout=120)
    ok = rc == 0
    print(out.rstrip() if ok else out[-3000:])
    print(f"  sandbox + write guard -> {'PASS' if ok else 'FAIL'}")
    return ok
