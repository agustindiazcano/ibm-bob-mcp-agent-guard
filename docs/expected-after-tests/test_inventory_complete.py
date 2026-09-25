"""Full-coverage reference tests for shop/inventory.py — see docs/expected-after-tests/README.md."""

import pytest

from shop.inventory import Inventory


# --- add_product / get_stock ---

def test_add_product_and_get_stock():
    inv = Inventory()
    inv.add_product("sku-1", "Widget", 10)
    assert inv.get_stock("sku-1") == 10


def test_add_product_negative_stock_raises():
    inv = Inventory()
    with pytest.raises(ValueError):
        inv.add_product("sku-1", "Widget", -1)


def test_add_product_zero_stock_succeeds():
    # boundary: stock < 0 is False when stock == 0 (an out-of-stock product is valid)
    inv = Inventory()
    inv.add_product("sku-1", "Widget", 0)
    assert inv.get_stock("sku-1") == 0


def test_add_product_default_reorder_point_used_when_omitted():
    # kills a mutation of add_product's default reorder_point=5 -> 6:
    # stock=6 needs no reorder under the real default (6 <= 5 is False),
    # but would incorrectly need one under a mutated default of 6.
    inv = Inventory()
    inv.add_product("sku-1", "Widget", 6)
    assert inv.needs_reorder("sku-1") is False


def test_get_stock_unknown_sku_raises_keyerror():
    # match on the message: get_stock()'s own KeyError has to fire, not the
    # dict's built-in KeyError that "self._products[sku]" would raise anyway
    # if the explicit check were ever removed
    inv = Inventory()
    with pytest.raises(KeyError, match="Unknown SKU"):
        inv.get_stock("missing-sku")


# --- reserve ---

def test_reserve_reduces_stock():
    inv = Inventory()
    inv.add_product("sku-1", "Widget", 10)
    inv.reserve("sku-1", 3)
    assert inv.get_stock("sku-1") == 7


def test_reserve_exact_remaining_stock_succeeds():
    # boundary: product.stock < qty is False when stock == qty
    inv = Inventory()
    inv.add_product("sku-1", "Widget", 5)
    inv.reserve("sku-1", 5)
    assert inv.get_stock("sku-1") == 0


def test_reserve_zero_qty_raises():
    inv = Inventory()
    inv.add_product("sku-1", "Widget", 10)
    with pytest.raises(ValueError):
        inv.reserve("sku-1", 0)


def test_reserve_negative_qty_raises():
    inv = Inventory()
    inv.add_product("sku-1", "Widget", 10)
    with pytest.raises(ValueError):
        inv.reserve("sku-1", -1)


def test_reserve_unknown_sku_raises_keyerror():
    inv = Inventory()
    with pytest.raises(KeyError):
        inv.reserve("missing-sku", 1)


def test_reserve_insufficient_stock_raises_valueerror():
    inv = Inventory()
    inv.add_product("sku-1", "Widget", 3)
    with pytest.raises(ValueError):
        inv.reserve("sku-1", 4)


# --- restock ---

def test_restock_increases_stock():
    inv = Inventory()
    inv.add_product("sku-1", "Widget", 10)
    inv.restock("sku-1", 5)
    assert inv.get_stock("sku-1") == 15


def test_restock_zero_qty_raises():
    inv = Inventory()
    inv.add_product("sku-1", "Widget", 10)
    with pytest.raises(ValueError):
        inv.restock("sku-1", 0)


def test_restock_negative_qty_raises():
    inv = Inventory()
    inv.add_product("sku-1", "Widget", 10)
    with pytest.raises(ValueError):
        inv.restock("sku-1", -1)


def test_restock_unknown_sku_raises_keyerror():
    inv = Inventory()
    with pytest.raises(KeyError):
        inv.restock("missing-sku", 1)


# --- needs_reorder / low_stock_skus ---

def test_needs_reorder_true_at_reorder_point_boundary():
    # boundary: stock <= reorder_point (equal counts as needing reorder)
    inv = Inventory()
    inv.add_product("sku-1", "Widget", 5, reorder_point=5)
    assert inv.needs_reorder("sku-1") is True


def test_needs_reorder_false_above_reorder_point():
    inv = Inventory()
    inv.add_product("sku-1", "Widget", 6, reorder_point=5)
    assert inv.needs_reorder("sku-1") is False


def test_needs_reorder_unknown_sku_raises_keyerror():
    inv = Inventory()
    with pytest.raises(KeyError):
        inv.needs_reorder("missing-sku")


def test_low_stock_skus_includes_boundary_and_excludes_above():
    inv = Inventory()
    inv.add_product("low", "Low Stock", 5, reorder_point=5)
    inv.add_product("high", "High Stock", 20, reorder_point=5)
    assert inv.low_stock_skus() == ["low"]
