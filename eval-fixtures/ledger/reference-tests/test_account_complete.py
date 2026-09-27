"""Reference tests for ledger.account -- eval fixture E3's ceiling suite.

Not run by default (pytest.ini only collects tests/); copy these into
tests/ to measure the fixture's baseline/ceiling delta, same pattern as
docs/expected-after-tests/ for demo-repo.
"""
import pytest

from ledger.account import InsufficientFundsError, deposit, transfer, withdraw


def test_deposit_basic():
    assert deposit(100.0, 50.0) == 150.0


def test_deposit_rejects_non_positive_amount():
    with pytest.raises(ValueError):
        deposit(100.0, 0.0)
    with pytest.raises(ValueError):
        deposit(100.0, -10.0)


def test_withdraw_no_overdraft():
    new_balance, fee = withdraw(100.0, 30.0)
    assert new_balance == 70.0
    assert fee == 0.0


def test_withdraw_triggers_overdraft_fee_once():
    new_balance, fee = withdraw(50.0, 100.0)
    assert new_balance == -85.0
    assert fee == 35.0


def test_withdraw_already_overdrawn_no_second_fee():
    # Starting balance already negative: crossing zero again doesn't re-charge the fee.
    new_balance, fee = withdraw(-50.0, 30.0)
    assert new_balance == -80.0
    assert fee == 0.0


def test_withdraw_exceeding_overdraft_limit_raises():
    with pytest.raises(InsufficientFundsError):
        withdraw(-50.0, 60.0)


def test_withdraw_rejects_non_positive_amount():
    with pytest.raises(ValueError):
        withdraw(100.0, 0.0)


def test_transfer_moves_amount_between_balances():
    new_from, new_to = transfer(100.0, 50.0, 30.0)
    assert new_from == 70.0
    assert new_to == 80.0
