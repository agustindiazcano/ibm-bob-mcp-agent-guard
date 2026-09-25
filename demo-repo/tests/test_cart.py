"""Intentionally weak tests for the cart — used as demo fixture for RepoGuard."""

from shop.cart import Cart


def test_cart_add_and_total():
    # Only tests the happy path — remove, clear, duplicates, errors are uncovered
    cart = Cart()
    cart.add("sku-1", 2, 10.0)
    assert cart.total() == 20.0


def test_cart_is_empty():
    cart = Cart()
    assert cart.is_empty()
