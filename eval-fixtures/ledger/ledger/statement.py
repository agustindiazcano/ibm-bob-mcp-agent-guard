"""Statement formatting and categorization -- intentionally has gaps (eval fixture E3, D3)."""
from __future__ import annotations


def categorize(amount: float) -> str:
    """Return 'credit' for positive amounts, 'debit' for negative, 'zero' for 0."""
    if amount > 0:
        return "credit"
    if amount < 0:
        return "debit"
    return "zero"


def format_line(description: str, amount: float, balance: float) -> str:
    """Return one formatted statement line."""
    sign = "+" if amount >= 0 else "-"
    return f"{description}: {sign}${abs(amount):.2f} (balance: ${balance:.2f})"


def summarize(transactions: list[float]) -> dict[str, float]:
    """Return totals for credits, debits and the net."""
    credits = sum(t for t in transactions if t > 0)
    debits = sum(t for t in transactions if t < 0)
    return {"credits": round(credits, 2), "debits": round(debits, 2), "net": round(credits + debits, 2)}
