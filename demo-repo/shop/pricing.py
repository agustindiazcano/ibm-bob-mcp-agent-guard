"""Pricing logic — intentionally has gaps for demo purposes."""

from __future__ import annotations

MEMBER_DISCOUNT = 0.10
BULK_THRESHOLD = 10
BULK_DISCOUNT = 0.05


def calculate_discount(price: float, quantity: int, is_member: bool = False) -> float:
    """Return the total discount amount for a line item."""
    if quantity <= 0:
        raise ValueError("quantity must be positive")

    discount = 0.0

    if is_member:
        discount += price * MEMBER_DISCOUNT

    if quantity >= BULK_THRESHOLD:
        discount += price * BULK_DISCOUNT

    return round(discount, 2)


def apply_pricing(price: float, quantity: int, is_member: bool = False) -> float:
    """Return the final price after discounts."""
    discount = calculate_discount(price, quantity, is_member)
    return round((price - discount) * quantity, 2)


def apply_tax(subtotal: float, tax_rate: float = 0.08) -> float:
    """Return subtotal with tax applied."""
    if tax_rate < 0:
        raise ValueError("tax_rate cannot be negative")
    return round(subtotal * (1 + tax_rate), 2)


def format_price(amount: float, currency: str = "USD") -> str:
    """Return a formatted price string."""
    symbols = {"USD": "$", "EUR": "€", "GBP": "£"}
    symbol = symbols.get(currency, currency + " ")
    return f"{symbol}{amount:.2f}"
