"use client";

import { useRef, useState } from "react";
import { RepoForm } from "./components/RepoForm";
import { ActionBar } from "./components/ActionBar";
import { StreamLog } from "./components/StreamLog";
import { StatCards } from "./components/StatCards";
import { GapsList } from "./components/GapsList";
import { RiskTable } from "./components/RiskTable";
import { SummaryPanel } from "./components/SummaryPanel";
import { FixResultPanel } from "./components/FixResultPanel";
import { EndpointsList } from "./components/EndpointsList";
import { Card } from "./components/Card";
import styles from "./page.module.css";
import { fetchAnalyze, fetchSummary, streamFix, streamUrl } from "./lib/api";
import type { AnalyzeResponse, Dashboard, FixDone, FixFile, RepoFormValues, StreamEvent, SummaryResponse } from "./lib/types";
import { useDemoMode } from "./context/DemoModeContext";

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Demo Mode's canned Autofix replay: the real fix loop takes 5-10 real
// minutes against demo-repo (a genuine mutation-testing + LLM-call cost, not
// a UI limitation) -- too long for a live pitch. This plays back the same
// event shape run_fix_loop's on_event emits, compressed to ~5s, then reveals
// the real, previously-measured before/after (AGENTS.md §7), clearly
// labeled as Demo Mode by the same banner pattern as /results' mock data.
const DEMO_FILES = ["shop/inventory.py", "shop/api.py", "shop/pricing.py"];

const DEMO_BEFORE: Dashboard = {
  coverage: { percent: 60.264900662251655, covered_lines: 91, total_lines: 151 },
  gaps: { uncovered_files: [...DEMO_FILES, "shop/cart.py"], missing_lines_by_file: {} },
  mutation: { score: 20.25, killed: 16, survived: 63, total: 79 },
  risk: [
    { file: "shop/inventory.py", score: 0.537, reasons: ["uncovered branches", "highest uncovered-line ratio"] },
    { file: "shop/api.py", score: 0.344, reasons: ["untested endpoints"] },
    { file: "shop/pricing.py", score: 0.276, reasons: ["uncovered discount branches"] },
    { file: "shop/cart.py", score: 0.243, reasons: ["uncovered edge cases"] },
  ],
};

const DEMO_AFTER: Dashboard = {
  coverage: { percent: 100.0, covered_lines: 151, total_lines: 151 },
  gaps: { uncovered_files: [], missing_lines_by_file: {} },
  mutation: { score: 89.87, killed: 71, survived: 8, total: 79 },
  risk: [],
};

const DEMO_FIX_FILES: FixFile[] = [
  {
    path: "tests/test_inventory.py",
    status: "added",
    content: `import pytest
from shop.inventory import Inventory, Product, InsufficientStockError

def test_sell_below_zero_raises():
    inv = Inventory({"sku-1": 2})
    with pytest.raises(InsufficientStockError):
        inv.sell("sku-1", 5)

def test_inventory_boundary_conditions():
    inv = Inventory({"sku-1": 10})
    inv.reserve("sku-1", 10)
    assert inv.get_stock("sku-1") == 0
    assert inv.needs_reorder("sku-1", reorder_point=5) is True
`,
  },
  {
    path: "tests/test_api.py",
    status: "modified",
    content: `import pytest
from fastapi.testclient import TestClient
from shop.api import app

@pytest.fixture
def client():
    return TestClient(app)

def test_checkout_endpoint_returns_200(client):
    res = client.post("/checkout", json={"cart_id": "c1"})
    assert res.status_code == 200
    assert res.json()["status"] == "success"

def test_cart_add_negative_qty_rejected(client):
    res = client.post("/cart/add", json={"sku": "sku-1", "qty": -1})
    assert res.status_code == 422
`,
  },
  {
    path: "tests/test_pricing.py",
    status: "modified",
    content: `import pytest
from shop.pricing import apply_pricing, calculate_discount

def test_apply_pricing_bulk_and_non_member():
    assert apply_pricing(50.0, 10, is_member=False) == 475.0

def test_pricing_bulk_threshold_boundaries():
    assert calculate_discount(50.0, 9) == 0.0
    assert calculate_discount(50.0, 10) == 25.0
    assert calculate_discount(50.0, 11) == 27.5
`,
  },
];

const DEMO_CRITIC_NOTES = [
  `shop/inventory.py: I ran pytest on \`tests/test_inventory.py\` and across the entire test suite; all 19 tests in \`test_inventory.py\` passed cleanly (and all 24 tests overall passed).

### Critic Review Summary
- **Assertions**: Non-trivial, verifying exact values and strict boolean matches (\`is True\` / \`is False\`).
- **State isolation**: Every test instantiates independent \`Inventory\` and \`Product\` instances; no shared state or test-order dependencies exist.
- **Boundary conditions**:
- \`stock\` boundary at 0 (0 allowed, -1 rejected).
- \`qty\` non-positive boundaries at 0 and -1 for both \`reserve\` and \`restock\`.
- Exact stock reserve (\`qty == stock\`), insufficient stock (\`qty > stock\`), and sufficient stock (\`qty < stock\`).
- Strict reorder boundaries tested at $n-1$, $n$, and $n+1$ relative to \`reorder_point\` (both for \`needs_reorder\` and \`low_stock_skus\`).
- **Exception verification**: All exception tests (\`ValueError\` and \`KeyError\`) verify both exception type and exact error message formatting.

**Verdict**: APPROVED`,
  `shop/api.py: I have reviewed \`tests/test_api.py\` and the target module \`shop/api.py\`.

### Quality & Correctness Checks
1. **Pass/Fail Verification**: \`pytest tests/test_api.py\` ran and all 15 tests passed cleanly (as did the full test suite).
2. **Assertion Quality**: No trivial assertions (\`assert True\` or empty checks); all endpoints verify HTTP status codes and exact JSON response payloads.
3. **State Isolation**: Autouse fixture \`reset_state\` properly resets mutable globals (\`_cart\` and \`_inventory._products\`) before and after each test.
4. **Boundary & Error Cases**:
- Zero and negative quantities/prices tested on \`/cart/add\`.
- Unknown SKU (404) and known SKU (200) tested on \`/inventory/{sku}\`.
- Unknown SKU (400) and zero restock quantity (400) tested on \`/inventory/restock\`.
- Exact error message formatting is verified (\`detail\` fields tested precisely, not just HTTP error status code).
- Checkout tax calculation tested with default rate, custom rate, and non-round decimal rate to verify rounding and precision.

VERDICT: **APPROVED**`,
  `shop/pricing.py: ### Test Review: \`tests/test_pricing.py\` for \`shop/pricing.py\`

#### Evaluation:
1. **Initial Verification**: Ran pytest on \`tests/test_pricing.py\` and the entire test suite; all passed.
2. **Assertion Quality**:
- Exact value comparisons used throughout; no assertion-free tests or weak truthy assertions.
- Exception handling asserts exact exception types and exact message strings using regex boundaries (\`^...$\`).
3. **State Isolation**:
- Functions are purely functional with no shared mutable state or inter-test ordering dependencies.
4. **Boundary & Edge Conditions**:
- \`quantity <= 0\` tested at 0 and -1.
- \`quantity >= BULK_THRESHOLD\` tested across the full boundary range: $n - 1$ (9), $n$ (10), and $n + 1$ (11).
- \`tax_rate < 0\` tested at $-0.01$ and $0.0$.
- Added test coverage for default parameter values (\`is_member=False\` in \`apply_pricing\`, default \`currency="USD"\` in \`format_price\`).
- Added test coverage for bulk discounting and combined discounting under \`apply_pricing\`.
- Verified 2-decimal rounding logic across \`calculate_discount\`, \`apply_pricing\`, \`apply_tax\`, and string formatting in \`format_price\`.

#### Test Run Results:
- \`tests/test_pricing.py\`: 22 passed in 0.03s.
- Full test suite: 58 passed in 0.04s.

**Verdict: APPROVED**`,
];

const DEFAULT_VALUES: RepoFormValues = {
  repoPath: "./demo-repo",
  mutation: false,
  gateThreshold: 80,
  provider: "vertex",
  swarm: true,
};

export default function Home() {
  const { demoMode } = useDemoMode();
  const [values, setValues] = useState<RepoFormValues>(DEFAULT_VALUES);
  const [busy, setBusy] = useState(false);
  const [autofixing, setAutofixing] = useState(false);
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [fix, setFix] = useState<FixDone | null>(null);
  // The threshold the shown result was measured against, so editing the
  // input afterwards doesn't relabel an old PASS/FAIL.
  const [ranThreshold, setRanThreshold] = useState(DEFAULT_VALUES.gateThreshold);
  // Whether the /api/analyze call in flight runs mutation testing; null when
  // none is in flight. Drives StreamLog's "still measuring" line.
  const [analyzing, setAnalyzing] = useState<{ mutation: boolean } | null>(null);
  const runRef = useRef(0);

  // The summary is fetched here rather than in a SummaryPanel effect because
  // StrictMode runs effects twice in dev, which doubled the paid watsonx.ai call.
  async function loadSummary(data: AnalyzeResponse, run: number, provider?: string, modelId?: string) {
    let next: SummaryResponse;
    try {
      next = await fetchSummary(data, provider, modelId);
    } catch (err) {
      next = {
        ok: false,
        text: "",
        error: err instanceof Error ? err.message : String(err),
        provider: "",
      };
    }
    if (runRef.current === run) {
      setSummary(next);
    }
  }

  async function runAnalyze(gateThreshold: number, mutation: boolean) {
    const run = ++runRef.current;
    setRanThreshold(gateThreshold);
    setAnalyzing({ mutation });
    setBusy(true);
    setError(null);
    setEvents([]);
    setResult(null);
    setSummary(null);
    setFix(null);

    const source = new EventSource(streamUrl(values.repoPath, gateThreshold));
    source.onmessage = (msg) => {
      const event = JSON.parse(msg.data) as StreamEvent;
      setEvents((prev) => [...prev, event]);
      if (event.type === "done" || event.type === "error") {
        source.close();
      }
    };
    source.onerror = () => source.close();

    try {
      const data = await fetchAnalyze({ ...values, gateThreshold, mutation });
      setResult(data);
      // Not awaited: the summary must never hold up or fail the dashboard.
      void loadSummary(data, run, values.provider, values.modelId);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setAnalyzing(null);
      setBusy(false);
    }
  }

  async function runAutofix() {
    ++runRef.current;
    setBusy(true);
    setAutofixing(true);
    setError(null);
    setEvents([]);
    setResult(null);
    setSummary(null);
    setFix(null);

    try {
      await streamFix(values, (event) => {
        if (event.type === "heartbeat") {
          return;
        }
        setEvents((prev) => [...prev, event]);
        if (event.type === "done") {
          setFix(event.data as unknown as FixDone);
        } else if (event.type === "error") {
          setError(String(event.data.message));
        }
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setAutofixing(false);
      setBusy(false);
    }
  }

  async function simulateAutofix() {
    const run = ++runRef.current;
    setBusy(true);
    setAutofixing(true);
    setError(null);
    setEvents([]);
    setResult(null);
    setSummary(null);
    setFix(null);

    const push = (type: StreamEvent["type"], data: Record<string, unknown> = {}) => {
      if (runRef.current !== run) return;
      setEvents((prev) => [...prev, { type, data }]);
    };

    push("start", { repo_path: values.repoPath, provider: "vertex" });
    await sleep(400);
    push("baseline_start", {});
    await sleep(600);
    push("baseline_done", { dashboard: DEMO_BEFORE, files: DEMO_FILES });
    for (const file of DEMO_FILES) {
      await sleep(500);
      push("writer_start", { file });
      await sleep(500);
      push("critic_start", { file });
    }
    await sleep(500);
    push("remeasure_start", {});
    await sleep(300);
    push("remeasure_done", { passed_gate: true });

    if (runRef.current !== run) return;
    const doneData: FixDone = {
      provider: "vertex",
      before: DEMO_BEFORE,
      after: DEMO_AFTER,
      files_attempted: DEMO_FILES,
      files: DEMO_FIX_FILES,
      critic_notes: DEMO_CRITIC_NOTES,
      evidence: "",
    };
    setEvents((prev) => [...prev, { type: "done", data: doneData as unknown as Record<string, unknown> }]);
    setFix(doneData);
    setAutofixing(false);
    setBusy(false);
  }

  function handleAutofixClick() {
    if (demoMode) {
      void simulateAutofix();
      return;
    }
    void runAutofix();
  }

  const streamEnded = events.some((e) => e.type === "done" || e.type === "error");
  const pending = autofixing
    ? "Running self-healing AI loop (measuring baseline + generating tests + verification)..."
    : analyzing && streamEnded
      ? analyzing.mutation
        ? "Running mutation testing — this can take several minutes"
        : "Finishing the analysis"
      : undefined;

  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <h1 className={styles.title}>TestMind AI</h1>
        <p className={styles.subtitle}>
          Self-Healing Test Suites & Quality Gate for Python · Measures real test effectiveness with AST mutation testing & closes coverage gaps with AI.
        </p>
      </header>
      <Card title="Analyze a repository">
        <RepoForm values={values} onChange={setValues} disabled={busy} />
        <ActionBar
          busy={busy}
          isAnalyzing={analyzing !== null}
          isAutofixing={autofixing}
          onAnalyze={() => runAnalyze(values.gateThreshold, values.mutation)}
          // Like `repoguard gate`: a coverage-only check, never mutation.
          onGate={() => runAnalyze(values.gateThreshold, false)}
          onAutofix={handleAutofixClick}
          swarm={values.swarm ?? true}
          onToggleSwarm={() => setValues({ ...values, swarm: !(values.swarm ?? true) })}
        />
      </Card>
      {error && (
        <div className={styles.alert} role="alert">
          <div>
            <strong>Error: </strong>
            {error}
          </div>
          {error.toLowerCase().includes("503") && (
            <p style={{ marginTop: "6px", fontSize: "12px", opacity: 0.9 }}>
              Tip: HTTP 503 from Autofix means <code>REPOGUARD_FIX_TOKEN</code> is not enabled on this server or AI provider credentials (watsonx.ai or Vertex AI) are missing.
            </p>
          )}
          {error.toLowerCase().includes("401") && (
            <p style={{ marginTop: "6px", fontSize: "12px", opacity: 0.9 }}>
              Tip: HTTP 401 indicates the provided Autofix token does not match the server&rsquo;s <code>REPOGUARD_FIX_TOKEN</code>. Click <strong>⚙️ Config</strong> in the top navigation to update your token.
            </p>
          )}
        </div>
      )}
      <StreamLog events={events} pending={pending} />
      {fix && demoMode && (
        <p style={{ marginTop: "-8px", marginBottom: "8px", fontSize: "12px", opacity: 0.8 }}>
          🎬 Demo Mode — simulated timing, real measured numbers (see <code>AGENTS.md §7</code>).
        </p>
      )}
      {fix && <FixResultPanel fix={fix} />}
      {!result && !fix && !busy && !error && events.length === 0 && (
        <p className={styles.empty}>
          Enter a repo path on the backend&rsquo;s machine and press Analyze to measure it.
        </p>
      )}
      {result && (
        <div className={styles.resultSection}>
          <StatCards result={result} gateThreshold={ranThreshold} />
          <div className={styles.columns}>
            <GapsList gaps={result.gaps} />
            <RiskTable risk={result.risk} />
          </div>
          <EndpointsList endpoints={result.endpoints} />
          <SummaryPanel summary={summary} />
        </div>
      )}
    </main>
  );
}

