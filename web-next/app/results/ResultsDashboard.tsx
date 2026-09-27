"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useDemoMode } from "../context/DemoModeContext";
import { EndpointsList } from "../components/EndpointsList";
import { RiskTable } from "../components/RiskTable";
import { ChartSlot } from "./ChartSlot";
import { FlakyTests } from "./FlakyTests";
import {
  fetchProjects,
  fetchView,
  type EndpointRow,
  type FlakyRow,
  type HistoryView,
  type Loaded,
  type OperatorRow,
  type Project,
  type RiskHeatmapRow,
  type Row,
  type SurvivorRow,
  type TrendRow,
} from "./history";
import {
  MOCK_ENDPOINTS,
  MOCK_FLAKY,
  MOCK_OPERATORS,
  MOCK_PROJECT,
  MOCK_PROJECTS,
  MOCK_RISK_HEATMAP,
  MOCK_SURVIVORS,
  MOCK_TREND,
} from "./mockData";
import { OperatorsChart } from "./OperatorsChart";
import { SurvivorsTable } from "./SurvivorsTable";
import { TrendChart } from "./TrendChart";
import styles from "./results.module.css";

// Demo Mode's canned response per view -- fix-effect has no mock yet (no
// real fix_sessions table exists either way, see PENDING.md), so it stays
// empty like the real backend's honest "nothing recorded" response.
const MOCK_VIEWS: Record<HistoryView, Row[]> = {
  trend: MOCK_TREND,
  operators: MOCK_OPERATORS,
  "risk-heatmap": MOCK_RISK_HEATMAP,
  "fix-effect": [],
  endpoints: MOCK_ENDPOINTS,
  survivors: MOCK_SURVIVORS,
  flaky: MOCK_FLAKY,
};

// Real-mode cache: the last successfully-fetched projects/views, so opening
// /results shows something immediately instead of a loading flash or an
// error banner, until a real fetchProjects()/fetchView() call succeeds and
// replaces it. Never used in Demo Mode. localStorage, not a JWT -- this is
// cached read data for one browser, not an auth credential to verify.
const CACHE_KEY = "testmind_results_cache_v1";

type ResultsCache = { projects: Project[]; selected: string; views: Partial<Record<HistoryView, Row[]>> };

function loadResultsCache(): ResultsCache | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    return raw ? (JSON.parse(raw) as ResultsCache) : null;
  } catch {
    return null;
  }
}

function patchResultsCache(patch: Partial<ResultsCache>) {
  try {
    const current = loadResultsCache() ?? { projects: [], selected: "", views: {} };
    const next: ResultsCache = {
      projects: patch.projects ?? current.projects,
      selected: patch.selected ?? current.selected,
      views: { ...current.views, ...(patch.views ?? {}) },
    };
    localStorage.setItem(CACHE_KEY, JSON.stringify(next));
  } catch {
    // Private browsing, quota, etc. -- caching is a convenience, never required.
  }
}

type SlotSpec = {
  view: HistoryView;
  title: string;
  question: string;
  form: string;
  wide?: boolean;
};

// The six views from docs/DATA_PLATFORM.md §6, in its order and layout.
const SLOTS: SlotSpec[] = [
  {
    view: "trend",
    title: "Coverage vs. mutation score per commit",
    question: "Is the suite getting better at catching bugs, or just running more lines?",
    form: "Two lines, shaded gap",
    wide: true,
  },
  {
    view: "operators",
    title: "Survival by mutation operator",
    question: "Which kinds of bugs slip through?",
    form: "Sorted horizontal bars",
  },
  {
    view: "fix-effect",
    title: "Before / after each fix run",
    question: "Did the AI-written tests actually move the score, and by how much?",
    form: "Slope chart",
  },
  {
    view: "risk-heatmap",
    title: "File risk over time",
    question: "Where is risk concentrating?",
    form: "Heatmap, file × run",
    wide: true,
  },
  {
    view: "endpoints",
    title: "Untested Endpoints",
    question: "Which API routes lack test coverage?",
    form: "List",
  },
  {
    view: "survivors",
    title: "Persistent survivors",
    question: "Which weak spots have never been caught?",
    form: "Table",
  },
  {
    view: "flaky",
    title: "Flaky tests",
    question: "Which tests are untrustworthy signals?",
    form: "Table",
  },
];

type Views = Record<HistoryView, Loaded<Row[]>>;

function allViews(state: Loaded<Row[]>): Views {
  return Object.fromEntries(SLOTS.map((s) => [s.view, state])) as Views;
}

const BANNERS: Record<string, { title: string; text: string }> = {
  "no-api": {
    title: "Run history isn't on this backend yet",
    text: "These charts read stored runs per project. They fill in once the database and its /api/projects routes ship (Phase 17). Single-run results are on Analyze today.",
  },
  "no-db": {
    title: "This backend has no database configured",
    text: "Runs are only stored when the backend has a database. Until then, single-run results are on Analyze.",
  },
  empty: {
    title: "No projects yet",
    text: "A project appears here once its first run is stored.",
  },
};

function latestRun(rows: Row[]): TrendRow | null {
  const trend = rows as TrendRow[];
  return trend.reduce<TrendRow | null>((latest, r) => (!latest || r.started_at > latest.started_at ? r : latest), null);
}

function Kpis({ trend }: { trend: Loaded<Row[]> }) {
  const run = trend.status === "ok" ? latestRun(trend.data) : null;
  const empty = trend.status === "loading" ? "…" : "—";
  const tiles = [
    { label: "Line coverage", value: run ? `${run.coverage_pct.toFixed(1)}%` : empty },
    { label: "Mutation score", value: run?.mutation_pct != null ? `${run.mutation_pct.toFixed(2)}%` : run ? "Not run" : empty },
    {
      label: "Coverage − mutation",
      value: run?.coverage_minus_mutation_pp != null ? `${run.coverage_minus_mutation_pp.toFixed(2)} pp` : run ? "—" : empty,
    },
    { label: "Quality gate", value: run ? (run.passed_gate ? "PASS" : "FAIL") : empty },
  ];
  return (
    <div className={styles.kpis}>
      {tiles.map((t) => (
        <div key={t.label} className={styles.kpi}>
          <span className={styles.kpiLabel}>{t.label}</span>
          <strong className={styles.kpiValue}>{t.value}</strong>
          <span className={styles.kpiDetail}>{run ? `Latest run · ${run.commit_sha?.slice(0, 7) ?? "no commit"}` : "No runs yet"}</span>
        </div>
      ))}
    </div>
  );
}

export function ResultsDashboard() {
  const { demoMode } = useDemoMode();
  const [projects, setProjects] = useState<Loaded<Project[]>>({ status: "loading" });
  const [selected, setSelected] = useState("");
  const [views, setViews] = useState<Views>(() => allViews({ status: "loading" }));
  const selectRef = useRef(0);

  function selectProject(slug: string) {
    const pick = ++selectRef.current;
    setSelected(slug);
    setViews(allViews({ status: "loading" }));
    patchResultsCache({ selected: slug });
    for (const { view } of SLOTS) {
      void fetchView(slug, view).then((state) => {
        // Drop responses for a project the user has already switched away from.
        if (selectRef.current === pick) {
          setViews((prev) => ({ ...prev, [view]: state }));
          if (state.status === "ok") {
            patchResultsCache({ views: { [view]: state.data } });
          }
        }
      });
    }
  }

  // Demo Mode: only the last project (MOCK_PROJECT) has a canned story --
  // the other two are placeholders that honestly show "no runs yet", same
  // as a real empty project would. Nothing is selected by default.
  function selectDemoProject(slug: string) {
    ++selectRef.current;
    setSelected(slug);
    const hasData = slug === MOCK_PROJECT.slug;
    setViews(
      Object.fromEntries(
        SLOTS.map((s) => [s.view, { status: "ok", data: hasData ? MOCK_VIEWS[s.view] : [] }]),
      ) as Views,
    );
  }

  useEffect(() => {
    if (demoMode) {
      ++selectRef.current;
      setProjects({ status: "ok", data: MOCK_PROJECTS });
      setSelected("");
      setViews(allViews({ status: "ok", data: [] }));
      return;
    }
    // Show cached data immediately (last real fetch this browser saw) while
    // the real request is in flight, instead of a loading flash. Replaced
    // the moment a real "ok" response comes back; if the backend is
    // unreachable, the cached view just stays on screen.
    const cached = loadResultsCache();
    if (cached && cached.projects.length > 0) {
      setProjects({ status: "ok", data: cached.projects });
      setSelected(cached.selected);
      setViews(
        Object.fromEntries(
          SLOTS.map((s) => [
            s.view,
            cached.views[s.view] ? { status: "ok", data: cached.views[s.view]! } : { status: "loading" },
          ]),
        ) as Views,
      );
    }

    void fetchProjects().then((state) => {
      if (state.status === "ok") {
        setProjects(state);
        if (state.data.length > 0) {
          patchResultsCache({ projects: state.data });
          selectProject(state.data[0].slug);
        } else {
          setViews(allViews({ status: "ok", data: [] }));
        }
      } else if (!cached) {
        setProjects(state);
        setViews(allViews(state));
      }
    });
    // selectProject only touches state setters and a ref, safe to omit.
  }, [demoMode]);

  // Demo Mode never shows a real error/unavailable banner -- even a stale
  // one from a previous real-mode fetch, for the one render before the
  // demoMode effect clears it. It has its own "Select a repo" prompt above.
  const bannerKey = demoMode
    ? null
    : projects.status === "unavailable"
      ? projects.reason.kind
      : projects.status === "ok" && projects.data.length === 0
        ? "empty"
        : null;
  const banner = bannerKey ? BANNERS[bannerKey] : null;
  const projectList = projects.status === "ok" ? projects.data : [];

  return (
    <>
      {!demoMode && projects.status === "unavailable" && !banner && (
        <p className={styles.alert} role="alert">
          {projects.reason.message}
        </p>
      )}
      {banner && (
        <div className={styles.banner} role="status">
          <strong>{banner.title}</strong>
          <span>{banner.text}</span>
          <Link href="/" className={styles.bannerLink}>
            Run an analysis →
          </Link>
        </div>
      )}
      {demoMode && (
        <div className={styles.banner} role="status">
          <strong>Demo Mode — sample data</strong>
          <span>These charts show canned data illustrating this project&rsquo;s real, measured before/after story, not a live query. Turn off Demo Mode for the real API.</span>
        </div>
      )}

      <div className={styles.filters}>
        <label className={styles.filter}>
          <span>Project</span>
          <select
            value={selected}
            onChange={(e) => (demoMode ? selectDemoProject(e.target.value) : selectProject(e.target.value))}
            disabled={projectList.length === 0}
          >
            {(projectList.length === 0 || (demoMode && !selected)) && (
              <option value="">
                {projectList.length === 0 ? (projects.status === "loading" ? "Loading…" : "No projects") : "Select a repo…"}
              </option>
            )}
            {projectList.map((p) => (
              <option key={p.slug} value={p.slug}>
                {p.slug}
              </option>
            ))}
          </select>
        </label>
      </div>

      {demoMode && !selected ? (
        <div className={styles.banner} role="status">
          <strong>Select a repo above to see its analytics.</strong>
        </div>
      ) : (
        <>
      <Kpis trend={views.trend} />

      <div className={styles.grid}>
        {SLOTS.map((s, i) => {
          const state = views[s.view];
          return (
          <ChartSlot
            key={s.view}
            index={i + 1}
            title={s.title}
            question={s.question}
            form={s.form}
            source={`/${s.view}`}
            state={state}
            wide={s.wide}
          >
            {s.view === "trend" && state.status === "ok" && state.data.length > 0 && (
              <TrendChart rows={state.data as TrendRow[]} />
            )}
            {s.view === "operators" && state.status === "ok" && state.data.length > 0 && (
              <OperatorsChart operators={state.data as OperatorRow[]} />
            )}
            {s.view === "risk-heatmap" && state.status === "ok" && state.data.length > 0 && (
              <RiskTable
                risk={(state.data as RiskHeatmapRow[]).map((r) => ({
                  file: r.file_path,
                  score: r.score,
                  reasons: r.reasons,
                }))}
              />
            )}
            {s.view === "endpoints" && state.status === "ok" && state.data.length > 0 && (
              <EndpointsList endpoints={state.data as EndpointRow[]} />
            )}
            {s.view === "survivors" && state.status === "ok" && state.data.length > 0 && (
              <SurvivorsTable survivors={state.data as SurvivorRow[]} />
            )}
            {s.view === "flaky" && state.status === "ok" && state.data.length > 0 && (
              <FlakyTests tests={state.data as FlakyRow[]} />
            )}
          </ChartSlot>
        )})}
      </div>
        </>
      )}
    </>
  );
}
