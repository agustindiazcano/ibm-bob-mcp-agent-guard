"""Reference tests for ledger.interest -- eval fixture E3's ceiling suite.
See test_account_complete.py for how these are used."""
import pytest

from ledger.interest import apply_tier_bonus, compound_interest, compute_interest


def test_compute_interest_basic():
    assert compute_interest(1000.0, 0.05, 365) == 50.0


def test_compute_interest_rejects_negative_principal():
    with pytest.raises(ValueError):
        compute_interest(-1.0, 0.05, 10)


def test_compute_interest_rejects_negative_days():
    with pytest.raises(ValueError):
        compute_interest(1000.0, 0.05, -1)


def test_compound_interest_basic():
    assert compound_interest(1000.0, 0.06, 1, 12) == 61.68


def test_compound_interest_rejects_non_positive_times_per_period():
    with pytest.raises(ValueError):
        compound_interest(1000.0, 0.06, 1, 0)


def test_apply_tier_bonus_top_tier():
    assert apply_tier_bonus(15000, 0.03) == 0.05


def test_apply_tier_bonus_mid_tier():
    assert apply_tier_bonus(5000, 0.03) == 0.04


def test_apply_tier_bonus_base_tier():
    assert apply_tier_bonus(500, 0.03) == 0.03
