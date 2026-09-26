"""watsonx.ai-driven fix loop -- replaces the retired .bob/ orchestrator.

See .bob/DEPRECATED.md for what this replaces and why.
"""

from .orchestrator import FixResult, run_fix_loop

__all__ = ["FixResult", "run_fix_loop"]
