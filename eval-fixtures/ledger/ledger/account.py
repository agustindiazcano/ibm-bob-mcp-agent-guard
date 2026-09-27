"""Account ledger logic -- intentionally has gaps (eval fixture E3, D3)."""
from __future__ import annotations

OVERDRAFT_LIMIT = 100.0
OVERDRAFT_FEE = 35.0


class InsufficientFundsError(Exception):
    pass


def deposit(balance: float, amount: float) -> float:
    """Return the new balance after depositing amount."""
    if amount <= 0:
        raise ValueError("deposit amount must be positive")
    return round(balance + amount, 2)


def withdraw(balance: float, amount: float) -> tuple[float, float]:
    """Return (new_balance, fee_charged) after withdrawing amount.

    Allows the balance to go negative up to OVERDRAFT_LIMIT, charging
    OVERDRAFT_FEE only the first time it crosses zero. Raises if the
    withdrawal would exceed the overdraft limit.
    """
    if amount <= 0:
        raise ValueError("withdraw amount must be positive")

    new_balance = round(balance - amount, 2)
    fee = 0.0

    if new_balance < 0:
        if balance >= 0:
            fee = OVERDRAFT_FEE
            new_balance = round(new_balance - fee, 2)
        if new_balance < -OVERDRAFT_LIMIT:
            raise InsufficientFundsError("withdrawal exceeds overdraft limit")

    return new_balance, fee


def transfer(from_balance: float, to_balance: float, amount: float) -> tuple[float, float]:
    """Return (new_from_balance, new_to_balance) after transferring amount."""
    new_from, _fee = withdraw(from_balance, amount)
    new_to = deposit(to_balance, amount)
    return new_from, new_to
