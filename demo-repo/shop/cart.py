"""Shopping cart — intentionally has gaps for demo purposes."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CartItem:
    sku: str
    quantity: int
    unit_price: float

    @property
    def subtotal(self) -> float:
        return round(self.unit_price * self.quantity, 2)


class Cart:
    def __init__(self) -> None:
        self._items: dict[str, CartItem] = {}

    def add(self, sku: str, qty: int, price: float) -> None:
        if qty <= 0:
            raise ValueError("quantity must be positive")
        if price < 0:
            raise ValueError("price cannot be negative")
        if sku in self._items:
            self._items[sku].quantity += qty
        else:
            self._items[sku] = CartItem(sku=sku, quantity=qty, unit_price=price)

    def remove(self, sku: str) -> None:
        if sku not in self._items:
            raise KeyError(f"SKU {sku!r} not in cart")
        del self._items[sku]

    def total(self) -> float:
        return round(sum(item.subtotal for item in self._items.values()), 2)

    def item_count(self) -> int:
        return sum(item.quantity for item in self._items.values())

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def clear(self) -> None:
        self._items.clear()

    def items(self) -> list[CartItem]:
        return list(self._items.values())
