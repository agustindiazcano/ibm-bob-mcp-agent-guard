"""Multi-agent swarm fix loop (Phase 18) -- one lane per source file, each
run in its own sandbox, fanned in behind a single Gate re-measurement.

Sandbox/guard groundwork (S3) plus the lane state machine, blackboard and
thread pool (S4, see docs/MULTI_AGENT_SWARM.md) live here. The critic
stage, fan-in, Gate and --swarm CLI flag are S5 and later.
"""
