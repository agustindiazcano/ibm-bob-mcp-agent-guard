"""Multi-agent swarm fix loop (Phase 18) -- one lane per source file, each
run in its own sandbox, fanned in behind a single Gate re-measurement.

Only the sandbox/guard groundwork (Step S3, see docs/MULTI_AGENT_SWARM.md)
lives here so far; the lane state machine, blackboard and thread pool are
S4 and later.
"""
