"""FastAPI endpoints for the demo shop — intentionally has gaps for demo purposes."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .cart import Cart
from .pricing import apply_pricing, apply_tax
from .inventory import Inventory

app = FastAPI(title="Demo Shop API")
_inventory = Inventory()
_cart = Cart()


class AddItemRequest(BaseModel):
    sku: str
    quantity: int
    price: float
    is_member: bool = False


class RestockRequest(BaseModel):
    sku: str
    quantity: int


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.get("/cart")
def get_cart() -> dict:
    return {
        "items": [
            {"sku": i.sku, "qty": i.quantity, "unit_price": i.unit_price, "subtotal": i.subtotal}
            for i in _cart.items()
        ],
        "total": _cart.total(),
        "item_count": _cart.item_count(),
    }


@app.post("/cart/add")
def add_to_cart(req: AddItemRequest) -> dict:
    try:
        _cart.add(req.sku, req.quantity, req.price)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"total": _cart.total()}


@app.delete("/cart/clear")
def clear_cart() -> dict:
    _cart.clear()
    return {"message": "Cart cleared"}


@app.get("/inventory/{sku}")
def get_inventory(sku: str) -> dict:
    try:
        stock = _inventory.get_stock(sku)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"SKU {sku!r} not found")
    return {"sku": sku, "stock": stock}


@app.post("/inventory/restock")
def restock(req: RestockRequest) -> dict:
    try:
        _inventory.restock(req.sku, req.quantity)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"sku": req.sku, "new_stock": _inventory.get_stock(req.sku)}


@app.get("/checkout/total")
def checkout_total(tax_rate: float = 0.08) -> dict:
    subtotal = _cart.total()
    total_with_tax = apply_tax(subtotal, tax_rate)
    return {"subtotal": subtotal, "tax": round(total_with_tax - subtotal, 2), "total": total_with_tax}
