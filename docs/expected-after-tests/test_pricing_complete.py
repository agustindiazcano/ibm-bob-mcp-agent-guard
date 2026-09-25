"""Full-coverage reference tests for shop/pricing.py — see docs/expected-after-tests/README.md."""

import pytest

from shop.pricing import apply_pricing, apply_tax, calculate_discount, format_price


# --- calculate_discount ---

def test_calculate_discount_zero_quantity_raises():
    with pytest.raises(ValueError):
        calculate_discount(100.0, 0, is_member=False)


def test_calculate_discount_negative_quantity_raises():
    with pytest.raises(ValueError):
        calculate_discount(100.0, -1, is_member=False)


def test_calculate_discount_non_member_below_bulk_is_zero():
    assert calculate_discount(100.0, 1, is_member=False) == 0.0


def test_calculate_discount_default_is_member_is_false():
    # kills a mutation of the is_member=False default -> True: omitting the
    # kwarg must behave like the non-member path, not the member path
    assert calculate_discount(100.0, 1) == 0.0


def test_calculate_discount_member_below_bulk():
    assert calculate_discount(100.0, 1, is_member=True) == 10.0


def test_calculate_discount_non_member_at_bulk_threshold():
    # quantity == BULK_THRESHOLD (10) — boundary for the >= comparison
    assert calculate_discount(100.0, 10, is_member=False) == 5.0


def test_calculate_discount_non_member_just_below_bulk_threshold():
    # quantity == BULK_THRESHOLD - 1 — must NOT get the bulk discount
    assert calculate_discount(100.0, 9, is_member=False) == 0.0


def test_calculate_discount_member_and_bulk_combine():
    assert calculate_discount(100.0, 10, is_member=True) == 15.0


# --- apply_pricing ---

def test_apply_pricing_no_discount():
    assert apply_pricing(50.0, 2, is_member=False) == 100.0


def test_apply_pricing_member_discount():
    assert apply_pricing(100.0, 1, is_member=True) == 90.0


def test_apply_pricing_bulk_discount():
    assert apply_pricing(10.0, 10, is_member=False) == 95.0


def test_apply_pricing_member_and_bulk_discount():
    assert apply_pricing(10.0, 10, is_member=True) == 85.0


# --- apply_tax ---

def test_apply_tax_default_rate():
    assert apply_tax(100.0) == 108.0


def test_apply_tax_zero_rate_returns_subtotal():
    assert apply_tax(50.0, tax_rate=0.0) == 50.0


def test_apply_tax_negative_rate_raises():
    with pytest.raises(ValueError):
        apply_tax(100.0, tax_rate=-0.01)


def test_apply_tax_custom_rate():
    assert apply_tax(200.0, tax_rate=0.10) == 220.0


# --- format_price ---

def test_format_price_default_currency():
    assert format_price(9.5) == "$9.50"


def test_format_price_eur():
    assert format_price(9.5, "EUR") == "€9.50"


def test_format_price_gbp():
    assert format_price(9.5, "GBP") == "£9.50"


def test_format_price_unknown_currency_falls_back_to_code_prefix():
    assert format_price(9.5, "JPY") == "JPY 9.50"
