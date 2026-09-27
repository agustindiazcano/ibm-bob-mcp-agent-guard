"""Intentionally weak tests for account -- eval fixture E3 (D3)."""
from ledger.account import deposit, withdraw


def test_deposit_basic():
    # Only the positive-amount path -- the validation-error path is uncovered
    assert deposit(100.0, 50.0) == 150.0


def test_withdraw_basic():
    # Only the always-positive-balance path -- overdraft, fee and limit paths uncovered
    new_balance, _fee = withdraw(100.0, 30.0)
    assert new_balance == 70.0
