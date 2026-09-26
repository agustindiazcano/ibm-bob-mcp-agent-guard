"""Test doubles for exercising the AI stages without credentials.

Nothing here is reachable through ai_providers.get_provider(): a scripted
provider can only be injected explicitly (run_fix_loop(model=...)), so the
"unknown provider fails loud" guarantee (verify.py multicloud) still holds.
"""

from .scripted_provider import ScriptedProvider

__all__ = ["ScriptedProvider"]
