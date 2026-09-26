"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { ChartSlot } from "./ChartSlot";
import { fetchProjects, fetchView, type HistoryView, type Loaded, type Project, type Row, type TrendRow } from "./history";
import styles from "./results.module.css";

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
  const [projects, setProjects] = useState<Loaded<Project[]>>({ status: "loading" });
  const [selected, setSelected] = useState("");
  const [views, setViews] = useState<Views>(() => allViews({ status: "loading" }));
  const selectRef = useRef(0);

  function selectProject(slug: string) {
    const pick = ++selectRef.current;
    setSelected(slug);
    setViews(allViews({ status: "loading" }));
    for (const { view } of SLOTS) {
      void fetchView(slug, view).then((state) => {
        // Drop responses for a project the user has already switched away from.
        if (selectRef.current === pick) {
          setViews((prev) => ({ ...prev, [view]: state }));
        }
      });
    }
  }

  useEffect(() => {
    void fetchProjects().then((state) => {
      setProjects(state);
      if (state.status === "ok" && state.data.length > 0) {
        selectProject(state.data[0].slug);
      } else if (state.status === "ok") {
        setViews(allViews({ status: "ok", data: [] }));
      } else if (state.status === "unavailable") {
        setViews(allViews(state));
      }
    });
    // Runs once on mount; selectProject only touches state setters and a ref.
  }, []);

  const bannerKey =
    projects.status === "unavailable"
      ? projects.reason.kind
      : projects.status === "ok" && projects.data.length === 0
        ? "empty"
        : null;
  const banner = bannerKey ? BANNERS[bannerKey] : null;
  const projectList = projects.status === "ok" ? projects.data : [];

  return (
    <>
      {projects.status === "unavailable" && !banner && (
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

      <div className={styles.filters}>
        <label className={styles.filter}>
          <span>Project</span>
          <select
            value={selected}
            onChange={(e) => selectProject(e.target.value)}
            disabled={projectList.length === 0}
          >
            {projectList.length === 0 && <option value="">{projects.status === "loading" ? "Loading…" : "No projects"}</option>}
            {projectList.map((p) => (
              <option key={p.slug} value={p.slug}>
                {p.slug}
              </option>
            ))}
          </select>
        </label>
      </div>

      <Kpis trend={views.trend} />

      <div className={styles.grid}>
        {SLOTS.map((s, i) => (
          <ChartSlot
            key={s.view}
            index={i + 1}
            title={s.title}
            question={s.question}
            form={s.form}
            source={`/${s.view}`}
            state={views[s.view]}
            wide={s.wide}
          />
        ))}
      </div>
    </>
  );
}
