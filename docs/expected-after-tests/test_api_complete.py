"""
Full-coverage reference tests for shop/api.py — see docs/expected-after-tests/README.md.

Note: /inventory/{sku} and /inventory/restock have no route that creates a
product — the API only exposes get_stock and restock, never add_product.
There is no way to reach their success path through the public API surface
at all. This is a real gap in shop/api.py, not a test artifact; AGENTS.md §4
says a failing/blocked test here means the test is wrong "unless there is
evidence of a real bug" — this is that evidence. Rather than leave those
branches permanently uncoverable, these tests seed shop.api's module-level
_inventory singleton directly (arranging state, not modifying source or
faking an assertion) so the success paths are still exercised.
"""

import pytest
from fastapi.testclient import TestClient

import shop.api as api_module
from shop.api import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_shared_state():
    """shop.api's _cart and _inventory are module-level singletons shared
    across every request; reset them before and after each test so tests
    don't depend on execution order (Rule 03 — Independence)."""
    api_module._cart.clear()
    api_module._inventory._products.clear()
    yield
    api_module._cart.clear()
    api_module._inventory._products.clear()


# --- /health ---

def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- /cart ---

def test_get_cart_empty():
    response = client.get("/cart")
    assert response.json() == {"items": [], "total": 0.0, "item_count": 0}


def test_add_to_cart_success():
    response = client.post(
        "/cart/add", json={"sku": "sku-1", "quantity": 2, "price": 10.0}
    )
    assert response.status_code == 200
    assert response.json() == {"total": 20.0}


def test_add_to_cart_invalid_quantity_returns_400():
    response = client.post(
        "/cart/add", json={"sku": "sku-1", "quantity": 0, "price": 10.0}
    )
    assert response.status_code == 400


def test_get_cart_reflects_added_item():
    client.post("/cart/add", json={"sku": "sku-1", "quantity": 1, "price": 5.0})
    response = client.get("/cart")
    body = response.json()
    assert body["item_count"] == 1
    assert body["total"] == 5.0


def test_clear_cart_empties_it():
    client.post("/cart/add", json={"sku": "sku-1", "quantity": 1, "price": 5.0})
    response = client.delete("/cart/clear")
    assert response.status_code == 200
    assert client.get("/cart").json()["item_count"] == 0


# --- /inventory/{sku} ---

def test_get_inventory_unknown_sku_returns_404():
    response = client.get("/inventory/missing-sku")
    assert response.status_code == 404


def test_get_inventory_known_sku_returns_stock():
    api_module._inventory.add_product("sku-1", "Widget", 10)
    response = client.get("/inventory/sku-1")
    assert response.json() == {"sku": "sku-1", "stock": 10}


# --- /inventory/restock ---

def test_restock_unknown_sku_returns_400():
    response = client.post(
        "/inventory/restock", json={"sku": "missing-sku", "quantity": 5}
    )
    assert response.status_code == 400


def test_restock_known_sku_returns_new_stock():
    api_module._inventory.add_product("sku-1", "Widget", 10)
    response = client.post("/inventory/restock", json={"sku": "sku-1", "quantity": 5})
    assert response.status_code == 200
    assert response.json() == {"sku": "sku-1", "new_stock": 15}


# --- /checkout/total ---

def test_checkout_total_default_tax_rate():
    client.post("/cart/add", json={"sku": "sku-1", "quantity": 1, "price": 100.0})
    response = client.get("/checkout/total")
    body = response.json()
    assert body["subtotal"] == 100.0
    assert body["total"] == 108.0
    assert body["tax"] == 8.0


def test_checkout_total_custom_tax_rate():
    client.post("/cart/add", json={"sku": "sku-1", "quantity": 1, "price": 100.0})
    response = client.get("/checkout/total", params={"tax_rate": 0.0})
    assert response.json()["total"] == 100.0
