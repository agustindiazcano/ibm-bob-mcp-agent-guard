import type { Metadata } from "next";
import { SlideHeader, SlideShell } from "../components/site/Page";
import blocks from "../components/site/Blocks.module.css";

export const metadata: Metadata = {
  title: "Before / After",
  description: "Real test code from this repo: demo-repo's weak baseline vs. the reference suite that reaches 89.87% mutation score.",
};

const BEFORE = `# demo-repo/tests/test_pricing.py (real, weak baseline)
from shop.pricing import calculate_discount, apply_pricing

def test_calculate_discount_member():
    # Only tests the member path — bulk and
    # zero-quantity paths are uncovered
    result = calculate_discount(100.0, 1, is_member=True)
    assert result > 0

def test_apply_pricing_basic():
    # No edge cases, no boundary tests
    result = apply_pricing(50.0, 2)
    assert result == 100.0`;

const AFTER = `# docs/expected-after-tests/test_pricing_complete.py (real)
def test_calculate_discount_zero_quantity_raises():
    with pytest.raises(ValueError):
        calculate_discount(100.0, 0, is_member=False)

def test_calculate_discount_non_member_at_bulk_threshold():
    # quantity == BULK_THRESHOLD (10) — the >= boundary
    assert calculate_discount(100.0, 10, is_member=False) == 5.0

def test_calculate_discount_non_member_just_below_bulk_threshold():
    # quantity == BULK_THRESHOLD - 1 — must NOT get the discount
    assert calculate_discount(100.0, 9, is_member=False) == 0.0

def test_apply_tax_negative_rate_raises():
    with pytest.raises(ValueError):
        apply_tax(100.0, tax_rate=-0.01)

# ... 16 more, same file — every branch, every boundary`;

export default function CodeComparisonPage() {
  return (
    <SlideShell>
      <SlideHeader
        eyebrow="Before / after"
        title="Same file, two real test suites. One only runs the code; the other checks it."
        lead="2 tests → 20 tests for shop/pricing.py alone. Across the whole repo: 5 → 71 tests, mutation score 20.25% → 89.87%."
      />
      <div className={blocks.grid2}>
        <div className={blocks.tile}>
          <h3 className={blocks.tileTitle}>Before — weak, on purpose</h3>
          <pre className={blocks.pre}>{BEFORE}</pre>
        </div>
        <div className={blocks.tile}>
          <h3 className={blocks.tileTitle}>After — boundaries, errors, every branch</h3>
          <pre className={blocks.pre}>{AFTER}</pre>
        </div>
      </div>
    </SlideShell>
  );
}
