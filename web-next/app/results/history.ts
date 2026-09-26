import { apiBase, failure, request } from "../lib/api";

// Run-history client for /results. The routes are the planned ones in
// docs/DATA_PLATFORM.md §7, reading the §4.4 views (Phase 17, step A3.1);
// they don't exist on the backend yet. When they land, check every row type
// below against web/server.py's real responses and fix the types to match,
// never reshape the server's data here. Rows are rendered verbatim: no
// metric is computed in the browser.

export type Project = { slug: string; repo_url: string | null; created_at: string };

// v_run_trend. passed_gate is 0/1 because the view derives it with CASE.
export type TrendRow = {
  run_id: string;
  commit_sha: string | null;
  started_at: string;
  operators_hash: string;
  coverage_pct: number;
  mutation_pct: number | null;
  coverage_minus_mutation_pp: number | null;
  passed_gate: 0 | 1;
};

// v_survival_by_operator (latest run only).
export type OperatorRow = { operator: string; total: number; survived: number; survival_pct: number };

// v_fix_effect.
export type FixEffectRow = {
  id: string;
  provider: string;
  model_id: string;
  before_pct: number;
  after_pct: number;
  delta_pp: number;
};

// v_persistent_survivors.
export type SurvivorRow = {
  fingerprint: string;
  file_path: string;
  function_name: string;
  description: string;
  runs_seen: number;
  first_seen: string;
};

// v_flaky_tests.
export type FlakyRow = { commit_sha: string; test_id: string; distinct_outcomes: number; runs: number };

// risk-heatmap has no view in §4.4 (it reads risk_scores per run), so its
// row shape is whatever the backend defines; typed as generic rows until then.

export type HistoryView = "trend" | "operators" | "risk-heatmap" | "fix-effect" | "survivors" | "flaky";

export type Row = Record<string, unknown>;

export type Unavailable = {
  kind: "unreachable" | "no-api" | "no-db" | "not-found" | "error";
  message: string;
};

export type Loaded<T> = { status: "loading" } | { status: "ok"; data: T } | { status: "unavailable"; reason: Unavailable };

function unavailable(kind: Unavailable["kind"], message: string): Loaded<never> {
  return { status: "unavailable", reason: { kind, message } };
}

async function getJson<T>(path: string, what: string, missingRoute: Unavailable["kind"]): Promise<Loaded<T>> {
  let res: Response;
  try {
    res = await request(`${apiBase()}${path}`);
  } catch (err) {
    return unavailable("unreachable", err instanceof Error ? err.message : String(err));
  }
  if (res.ok) {
    return { status: "ok", data: (await res.json()) as T };
  }
  // §13 A3.1: 503 means "no database configured", distinct from "no runs yet" ([]).
  if (res.status === 503) {
    return unavailable("no-db", "Run history isn't configured on this backend: it has no database.");
  }
  const { message } = await failure(res, what);
  if (res.status === 404) {
    return unavailable(missingRoute, message);
  }
  return unavailable("error", message);
}

export function fetchProjects(): Promise<Loaded<Project[]>> {
  // A 404 here is FastAPI's default for an unknown route: the backend
  // predates Phase 17.
  return getJson<Project[]>("/api/projects", "projects", "no-api");
}

export function fetchView(slug: string, view: HistoryView): Promise<Loaded<Row[]>> {
  return getJson<Row[]>(`/api/projects/${encodeURIComponent(slug)}/${view}`, view, "not-found");
}
