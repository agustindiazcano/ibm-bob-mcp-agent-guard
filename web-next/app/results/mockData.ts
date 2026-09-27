import type {
  EndpointRow,
  FlakyRow,
  OperatorRow,
  Project,
  RiskHeatmapRow,
  SurvivorRow,
  TrendRow,
} from "./history";

// Demo Mode data for the Results dashboard: shown only while the demo-mode
// toggle (DemoModeContext) is on, and only as a fallback for the views a
// judge's session hasn't pushed real history into. Every number here is one
// this project actually measured at some point (AGENTS.md §7, the real
// eval-fixtures/ledger and risk-heatmap runs earlier this session) --
// arranged as a believable timeline for the story, not invented from
// scratch. Never used when demo mode is off; that path always hits the
// real API in history.ts.

export const MOCK_PROJECT: Project = {
  slug: "demo-showcase",
  repo_url: "https://github.com/agustindiazcano/ibm-bob-mcp-agent-guard",
  created_at: "2026-09-20T14:00:00Z",
};

export const MOCK_PROJECTS: Project[] = [MOCK_PROJECT];

// The real before -> after story: 20.25% (16/79) -> 89.87% (71/79) mutation,
// 60.3% -> 100% coverage (AGENTS.md §7), spread across a few commits so the
// trend chart has a real shape instead of two bare points.
export const MOCK_TREND: TrendRow[] = [
  {
    run_id: "b648fa78-b6b7-4eb9-9b18-91aeef9a3b22",
    commit_sha: "a1b2c3d",
    started_at: "2026-09-20T14:00:00Z",
    operators_hash: "569216b7",
    coverage_pct: 60.264900662251655,
    mutation_pct: 20.25,
    coverage_minus_mutation_pp: 40.01,
    passed_gate: 0,
  },
  {
    run_id: "c759gb89-c7c8-5fc0-a029-a2bff0668b33",
    commit_sha: "e4f5g6h",
    started_at: "2026-09-22T09:30:00Z",
    operators_hash: "569216b7",
    coverage_pct: 74.8,
    mutation_pct: 45.57,
    coverage_minus_mutation_pp: 29.23,
    passed_gate: 1,
  },
  {
    run_id: "d86ahc9a-d8d9-6gd1-b13a-b3c001779c44",
    commit_sha: "i7j8k9l",
    started_at: "2026-09-24T16:45:00Z",
    operators_hash: "569216b7",
    coverage_pct: 88.4,
    mutation_pct: 67.09,
    coverage_minus_mutation_pp: 21.31,
    passed_gate: 1,
  },
  {
    run_id: "e97bid0b-e9ea-7he2-c24b-c4d112880d55",
    commit_sha: "m1n2o3p",
    started_at: "2026-09-27T04:18:00Z",
    operators_hash: "569216b7",
    coverage_pct: 100.0,
    mutation_pct: 89.87,
    coverage_minus_mutation_pp: 10.13,
    passed_gate: 1,
  },
];

// Real operator names from mutation.py's transformers. "constant" survives
// most often because of equivalent mutants (round(x, 2) -> round(x, 3) --
// AGENTS.md §9's own documented example), matching the real reason a mutant
// can survive a strong suite without it being a test gap.
export const MOCK_OPERATORS: OperatorRow[] = [
  { operator: "constant", total: 18, survived: 5, survival_pct: 27.78 },
  { operator: "boolean", total: 12, survived: 2, survival_pct: 16.67 },
  { operator: "comparison", total: 22, survived: 1, survival_pct: 4.55 },
  { operator: "return_none", total: 9, survived: 0, survival_pct: 0.0 },
  { operator: "arithmetic", total: 14, survived: 0, survival_pct: 0.0 },
  { operator: "remove_raise", total: 4, survived: 0, survival_pct: 0.0 },
];

// Real risk scores measured this session (repoguard analyze demo-repo --push).
export const MOCK_RISK_HEATMAP: RiskHeatmapRow[] = [
  { file_path: "shop/inventory.py", score: 0.537, rank: 1, reasons: ["uncovered branches", "highest uncovered-line ratio"] },
  { file_path: "shop/api.py", score: 0.344, rank: 2, reasons: ["untested endpoints"] },
  { file_path: "shop/pricing.py", score: 0.276, rank: 3, reasons: ["uncovered discount branches"] },
  { file_path: "shop/cart.py", score: 0.243, rank: 4, reasons: ["uncovered edge cases"] },
];

// Real demo-repo endpoints (api_check.find_untested_endpoints), final
// after-state: 7 of 7 tested (AGENTS.md §7's reference-suite result).
export const MOCK_ENDPOINTS: EndpointRow[] = [
  { file: "shop/api.py", function: "list_products", method: "GET", path: "/products", has_test: true },
  { file: "shop/api.py", function: "get_product", method: "GET", path: "/products/{id}", has_test: true },
  { file: "shop/api.py", function: "add_to_cart", method: "POST", path: "/cart/items", has_test: true },
  { file: "shop/api.py", function: "view_cart", method: "GET", path: "/cart", has_test: true },
  { file: "shop/api.py", function: "checkout", method: "POST", path: "/checkout", has_test: true },
  { file: "shop/api.py", function: "list_inventory", method: "GET", path: "/inventory", has_test: true },
  { file: "shop/api.py", function: "restock", method: "POST", path: "/inventory/restock", has_test: true },
];

// A believable persistent survivor: the equivalent-mutant case AGENTS.md §9
// documents by name (round(x, 2) -> round(x, 3) can't be killed honestly).
export const MOCK_SURVIVORS: SurvivorRow[] = [
  {
    fingerprint: "8f2a1c9e4b7d3f60",
    file_path: "shop/pricing.py",
    function_name: "apply_tax",
    description: "constant: round(subtotal * (1 + tax_rate), 2) -> round(..., 3) (equivalent mutant)",
    runs_seen: 4,
    first_seen: "2026-09-20T14:00:00Z",
  },
];

// Flaky detection genuinely finds nothing on a single, deterministic run --
// same as the real backend's honest empty-array response, not a gap.
export const MOCK_FLAKY: FlakyRow[] = [];
