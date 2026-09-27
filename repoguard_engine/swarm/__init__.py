"""Multi-agent swarm fix loop (Phase 18) -- one lane per source file, each
run in its own sandbox, fanned in behind a single Gate re-measurement.

Sandbox/guard (S3), lane state machine + blackboard + thread pool (S4),
read-only critic with a JSON verdict and per-role providers (S5/S9), fan-in,
Gate, Publisher and Reporter (S6) -- see docs/MULTI_AGENT_SWARM.md.
Entry point: run_swarm(), exposed as `repoguard fix --swarm`.
"""

from .run import SwarmResult, run_swarm

__all__ = ["SwarmResult", "run_swarm"]
