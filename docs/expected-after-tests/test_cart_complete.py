"""Full-coverage reference tests for shop/cart.py — see docs/expected-after-tests/README.md."""

import pytest

from shop.cart import Cart, CartItem


# --- CartItem ---

def test_cart_item_subtotal():
    item = CartItem(sku="sku-1", quantity=3, unit_price=2.5)
    assert item.subtotal == 7.5


# --- Cart.add ---

def test_cart_add_creates_new_item():
    cart = Cart()
    cart.add("sku-1", 2, 10.0)
    assert cart.items()[0].quantity == 2


def test_cart_add_existing_sku_increments_quantity():
    cart = Cart()
    cart.add("sku-1", 2, 10.0)
    cart.add("sku-1", 3, 10.0)
    assert cart.item_count() == 5


def test_cart_add_zero_quantity_raises():
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add("sku-1", 0, 10.0)


def test_cart_add_negative_quantity_raises():
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add("sku-1", -1, 10.0)


def test_cart_add_negative_price_raises():
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add("sku-1", 1, -5.0)


def test_cart_add_zero_price_succeeds():
    # boundary: price < 0 is False when price == 0 (a free item is valid)
    cart = Cart()
    cart.add("sku-1", 1, 0.0)
    assert cart.total() == 0.0


# --- Cart.remove ---

def test_cart_remove_existing_sku():
    cart = Cart()
    cart.add("sku-1", 1, 10.0)
    cart.remove("sku-1")
    assert cart.is_empty()


def test_cart_remove_missing_sku_raises_keyerror():
    # match on the message: remove()'s own KeyError has to fire, not the
    # dict's built-in KeyError that "del self._items[sku]" would raise anyway
    # if the explicit check were ever removed
    cart = Cart()
    with pytest.raises(KeyError, match="not in cart"):
        cart.remove("missing-sku")


# --- Cart.total / item_count ---

def test_cart_total_multiple_items():
    cart = Cart()
    cart.add("sku-1", 2, 10.0)
    cart.add("sku-2", 1, 5.0)
    assert cart.total() == 25.0


def test_cart_item_count_multiple_items():
    cart = Cart()
    cart.add("sku-1", 2, 10.0)
    cart.add("sku-2", 3, 5.0)
    assert cart.item_count() == 5


# --- Cart.is_empty / clear / items ---

def test_cart_is_empty_true_when_new():
    cart = Cart()
    assert cart.is_empty()


def test_cart_is_empty_false_after_add():
    cart = Cart()
    cart.add("sku-1", 1, 10.0)
    assert cart.is_empty() is False


def test_cart_clear_empties_cart():
    cart = Cart()
    cart.add("sku-1", 1, 10.0)
    cart.clear()
    assert cart.is_empty()


def test_cart_items_returns_all_items():
    cart = Cart()
    cart.add("sku-1", 1, 10.0)
    cart.add("sku-2", 2, 5.0)
    skus = {item.sku for item in cart.items()}
    assert skus == {"sku-1", "sku-2"}
