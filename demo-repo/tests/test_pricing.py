"""Intentionally weak tests for pricing — used as demo fixture for RepoGuard."""

from shop.pricing import calculate_discount, apply_pricing


def test_calculate_discount_member():
    # Only tests the member path — bulk and zero-quantity paths are uncovered
    result = calculate_discount(100.0, 1, is_member=True)
    assert result > 0


def test_apply_pricing_basic():
    # No edge cases, no boundary tests, no non-member path
    result = apply_pricing(50.0, 2)
    assert result == 100.0
