# docs/expected-after-tests

Reference "good" test implementations for the demo-repo fixture.

These are the target tests that RepoGuard + Bob should produce after a fix cycle.
They are used as:
1. A fallback (Plan B) if the live demo Bob run doesn't complete in time
2. A quality benchmark to compare against Bob-generated tests

## Files

- `test_pricing_complete.py` — full coverage of `shop/pricing.py`
- `test_cart_complete.py` — full coverage of `shop/cart.py`
- `test_inventory_complete.py` — full coverage of `shop/inventory.py`
- `test_api_complete.py` — full coverage of `shop/api.py`
