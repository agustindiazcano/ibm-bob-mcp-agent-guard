---
name: mutation-hunting
description: >
  Strategy and patterns for writing mutation-resistant tests: how to detect surviving mutants,
  which assertion styles kill the most mutants, and how to interpret mutation score reports.
  Activate when improving test quality or analysing mutation testing output.
---

## What Is Mutation Testing?

A mutation tool (e.g. `mutmut`) makes small code changes ("mutants") — flipping `+` to `-`,
changing `>` to `>=`, removing a `return` — then runs the test suite. If the tests still pass,
the mutant **survived**, meaning the tests did not catch that class of bug.

**Mutation score** = killed mutants / total mutants × 100.
Target: ≥ 80% mutation score on critical modules.

## Common Surviving Mutant Patterns and Fixes

### Off-by-one (boundary mutations)

```python
# Mutant: > becomes >=   (survives if you only test non-boundary values)
# Fix: add a boundary-value test
@pytest.mark.parametrize("qty,should_raise", [(0, True), (1, False)])
def test_add_qty_boundary(qty, should_raise):
    cart = Cart()
    if should_raise:
        with pytest.raises(ValueError):
            cart.add("sku", qty=qty, price=1.0)
    else:
        cart.add("sku", qty=qty, price=1.0)
```

### Sign flip (arithmetic mutations)

```python
# Mutant: discount = price * rate  →  price - rate  (survives if you only assert non-zero)
# Fix: assert the exact numeric result
def test_discount_exact_value():
    assert calculate_discount(price=100.0, rate=0.2) == pytest.approx(20.0)
```

### Boolean negation (condition mutations)

```python
# Mutant: if is_member  →  if not is_member
# Fix: test both branches explicitly
def test_member_gets_discount():
    assert apply_pricing(price=100, is_member=True) < 100

def test_non_member_pays_full():
    assert apply_pricing(price=100, is_member=False) == 100
```

### Return-value deletion

```python
# Mutant: return result  →  return None
# Fix: always assert the return value, not just side effects
def test_process_order_returns_order_id():
    result = process_order({"sku": "A", "qty": 1})
    assert isinstance(result, str) and len(result) > 0
```

## Running Mutmut

```bash
# Install
pip install mutmut

# Run against a module
mutmut run --paths-to-mutate shop/pricing.py --tests-dir tests/

# See surviving mutants
mutmut results
mutmut show <id>

# HTML report
mutmut html
```

## Interpreting the Report

| Status | Meaning |
|---|---|
| Killed | Test suite caught the mutation ✅ |
| Survived | Tests did not catch it — add a targeted test ❌ |
| Timeout | Test ran too long — check for infinite loops |
| Suspicious | Test passed but with warnings |

## Prioritisation

Focus mutation-resistant tests on:
1. Pricing / financial calculations
2. Inventory boundary checks
3. Auth / permission guards
4. Any function with a `return` value that drives branching logic upstream
