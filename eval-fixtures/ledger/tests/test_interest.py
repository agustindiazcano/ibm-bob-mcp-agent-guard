"""Intentionally weak tests for interest -- eval fixture E3 (D3)."""
from ledger.interest import compute_interest


def test_compute_interest_basic():
    # Only one rate/day combination -- no validation errors, tiers or compounding
    result = compute_interest(1000.0, 0.05, 365)
    assert result == 50.0
