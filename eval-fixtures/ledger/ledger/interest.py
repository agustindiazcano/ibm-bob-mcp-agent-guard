"""Interest calculations -- intentionally has gaps (eval fixture E3, D3)."""
from __future__ import annotations

DAYS_PER_YEAR = 365


def compute_interest(principal: float, annual_rate: float, days: int) -> float:
    """Simple daily interest, rounded to cents."""
    if principal < 0:
        raise ValueError("principal cannot be negative")
    if days < 0:
        raise ValueError("days cannot be negative")
    daily_rate = annual_rate / DAYS_PER_YEAR
    return round(principal * daily_rate * days, 2)


def compound_interest(principal: float, annual_rate: float, periods: int, times_per_period: int = 12) -> float:
    """Compound interest earned, rounded to cents. periods is in years."""
    if times_per_period <= 0:
        raise ValueError("times_per_period must be positive")
    rate_per_period = annual_rate / times_per_period
    amount = principal * (1 + rate_per_period) ** (times_per_period * periods)
    return round(amount - principal, 2)


def apply_tier_bonus(balance: float, base_rate: float) -> float:
    """Higher balances earn a bonus rate tier."""
    if balance >= 10000:
        return base_rate + 0.02
    if balance >= 1000:
        return base_rate + 0.01
    return base_rate
