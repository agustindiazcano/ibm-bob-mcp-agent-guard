"""Inventory management — intentionally has gaps for demo purposes."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Product:
    sku: str
    name: str
    stock: int
    reorder_point: int = 5


class Inventory:
    def __init__(self) -> None:
        self._products: dict[str, Product] = {}

    def add_product(self, sku: str, name: str, stock: int, reorder_point: int = 5) -> None:
        if stock < 0:
            raise ValueError("stock cannot be negative")
        self._products[sku] = Product(sku=sku, name=name, stock=stock, reorder_point=reorder_point)

    def get_stock(self, sku: str) -> int:
        if sku not in self._products:
            raise KeyError(f"Unknown SKU: {sku!r}")
        return self._products[sku].stock

    def reserve(self, sku: str, qty: int) -> None:
        """Decrease stock by qty. Raises ValueError if insufficient stock."""
        if qty <= 0:
            raise ValueError("qty must be positive")
        product = self._products.get(sku)
        if product is None:
            raise KeyError(f"Unknown SKU: {sku!r}")
        if product.stock < qty:
            raise ValueError(f"Insufficient stock for {sku!r}: {product.stock} < {qty}")
        product.stock -= qty

    def restock(self, sku: str, qty: int) -> None:
        if qty <= 0:
            raise ValueError("qty must be positive")
        product = self._products.get(sku)
        if product is None:
            raise KeyError(f"Unknown SKU: {sku!r}")
        product.stock += qty

    def needs_reorder(self, sku: str) -> bool:
        return self.get_stock(sku) <= self._products[sku].reorder_point

    def low_stock_skus(self) -> list[str]:
        return [p.sku for p in self._products.values() if p.stock <= p.reorder_point]
