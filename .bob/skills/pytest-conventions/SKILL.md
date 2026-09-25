---
name: pytest-conventions
description: >
  Conventions for writing pytest tests in this project: file layout, fixture patterns,
  parametrize usage, conftest structure, and coverage pragmas. Activate when writing
  or reviewing any pytest test file.
---

## File Layout

- Test files live in `tests/` alongside the package they test.
- Name pattern: `test_<module>.py` mirrors `<module>.py` in the source package.
- One `conftest.py` per test directory; do not nest conftest files without a reason.

## Naming

```python
# function under test + scenario + expected result
def test_calculate_discount_zero_quantity_returns_full_price(): ...
def test_calculate_discount_negative_raises_value_error(): ...
```

## Fixtures

Define fixtures in `conftest.py`, not inline in test files, unless they are used only once.

```python
# conftest.py
import pytest
from shop.cart import Cart

@pytest.fixture
def empty_cart():
    return Cart()

@pytest.fixture
def cart_with_items(empty_cart):
    empty_cart.add("sku-1", qty=2, price=9.99)
    return empty_cart
```

## Parametrize

Use `@pytest.mark.parametrize` for multiple inputs to the same logic:

```python
@pytest.mark.parametrize("qty,expected", [
    (0,   0.0),
    (1,   9.99),
    (10, 99.90),
])
def test_cart_total(empty_cart, qty, expected):
    empty_cart.add("sku-1", qty=qty, price=9.99)
    assert empty_cart.total() == pytest.approx(expected)
```

## Exception Testing

```python
import pytest

def test_add_negative_qty_raises():
    cart = Cart()
    with pytest.raises(ValueError, match="quantity must be positive"):
        cart.add("sku-1", qty=-1, price=9.99)
```

## Coverage Pragmas

Use `# pragma: no cover` sparingly — only for:
- `if __name__ == "__main__":` blocks
- Abstract method stubs that are never called directly

Never use it to hide real logic from coverage.

## Running Tests

```bash
pytest                              # all tests
pytest tests/test_pricing.py       # single file
pytest --cov=shop --cov-report=term-missing   # with coverage
```
