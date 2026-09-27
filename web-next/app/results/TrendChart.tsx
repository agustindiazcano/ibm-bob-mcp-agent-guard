"use client";

import { useMemo, useState, type PointerEvent as ReactPointerEvent } from "react";
import type { TrendRow } from "./history";
import styles from "./charts.module.css";

// Coverage vs. mutation score per stored run (docs/DATA_PLATFORM.md §6, chart
// 1). Two lines + the shaded gap between them, both read verbatim from
// v_run_trend — nothing here is computed beyond plotting the given numbers.

const WIDTH = 640;
const HEIGHT = 220;
const PAD = { top: 16, right: 16, bottom: 26, left: 34 };
const PLOT_W = WIDTH - PAD.left - PAD.right;
const PLOT_H = HEIGHT - PAD.top - PAD.bottom;
const GRID_PCTS = [0, 50, 100];

function xAt(i: number, n: number): number {
  return n <= 1 ? PAD.left + PLOT_W / 2 : PAD.left + (PLOT_W * i) / (n - 1);
}

function yAt(pct: number): number {
  return PAD.top + PLOT_H * (1 - Math.min(Math.max(pct, 0), 100) / 100);
}

function linePath(points: { x: number; y: number }[]): string {
  return points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
}

// Mutation isn't always measured, so its line breaks into segments around
// any null point rather than interpolating across the gap.
function segments(values: (number | null)[], n: number): { x: number; y: number }[][] {
  const out: { x: number; y: number }[][] = [];
  let current: { x: number; y: number }[] = [];
  values.forEach((v, i) => {
    if (v == null) {
      if (current.length) out.push(current);
      current = [];
      return;
    }
    current.push({ x: xAt(i, n), y: yAt(v) });
  });
  if (current.length) out.push(current);
  return out;
}

function gapSegments(rows: TrendRow[], n: number): { x: number; yTop: number; yBottom: number }[][] {
  const out: { x: number; yTop: number; yBottom: number }[][] = [];
  let current: { x: number; yTop: number; yBottom: number }[] = [];
  rows.forEach((r, i) => {
    if (r.mutation_pct == null) {
      if (current.length) out.push(current);
      current = [];
      return;
    }
    current.push({ x: xAt(i, n), yTop: yAt(r.coverage_pct), yBottom: yAt(r.mutation_pct) });
  });
  if (current.length) out.push(current);
  return out;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function TrendChart({ rows }: { rows: TrendRow[] }) {
  const [hover, setHover] = useState<number | null>(null);
  const n = rows.length;

  const coverage = useMemo(() => rows.map((r, i) => ({ x: xAt(i, n), y: yAt(r.coverage_pct) })), [rows, n]);
  const mutationSegs = useMemo(() => segments(rows.map((r) => r.mutation_pct), n), [rows, n]);
  const gapSegs = useMemo(() => gapSegments(rows, n), [rows, n]);

  if (n === 0) {
    return null;
  }

  const active = hover != null ? rows[hover] : null;
  const activeX = hover != null ? xAt(hover, n) : 0;

  function handlePointer(e: ReactPointerEvent<SVGRectElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const relX = ((e.clientX - rect.left) / rect.width) * WIDTH;
    let nearest = 0;
    let best = Infinity;
    for (let i = 0; i < n; i++) {
      const d = Math.abs(xAt(i, n) - relX);
      if (d < best) {
        best = d;
        nearest = i;
      }
    }
    setHover(nearest);
  }

  return (
    <div className={styles.chartWrap}>
      <div className={styles.legend}>
        <span className={styles.legendItem}>
          <span className={styles.legendLine} style={{ background: "var(--accent)" }} aria-hidden />
          Coverage
        </span>
        <span className={styles.legendItem}>
          <span className={styles.legendLine} style={{ background: "var(--series-2)" }} aria-hidden />
          Mutation score
        </span>
      </div>
      <svg
        className={styles.svg}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label="Coverage and mutation score per stored run, over time"
        onPointerLeave={() => setHover(null)}
      >
        {GRID_PCTS.map((pct) => (
          <g key={pct}>
            <line className={styles.gridline} x1={PAD.left} x2={WIDTH - PAD.right} y1={yAt(pct)} y2={yAt(pct)} />
            <text className={styles.axisLabel} x={PAD.left - 6} y={yAt(pct)} textAnchor="end" dominantBaseline="middle">
              {pct}%
            </text>
          </g>
        ))}
        {gapSegs.map((seg, i) =>
          seg.length > 1 ? (
            <polygon
              key={i}
              fill="var(--text-muted)"
              fillOpacity={0.12}
              points={[
                ...seg.map((p) => `${p.x.toFixed(1)},${p.yTop.toFixed(1)}`),
                ...[...seg].reverse().map((p) => `${p.x.toFixed(1)},${p.yBottom.toFixed(1)}`),
              ].join(" ")}
            />
          ) : null,
        )}
        <path d={linePath(coverage)} fill="none" stroke="var(--accent)" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
        {mutationSegs.map((seg, i) => (
          <path key={i} d={linePath(seg)} fill="none" stroke="var(--series-2)" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
        ))}
        {coverage.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r={hover === i ? 5 : 3} fill="var(--accent)" stroke="var(--surface)" strokeWidth={2} />
        ))}
        {rows.map((r, i) =>
          r.mutation_pct == null ? null : (
            <circle
              key={i}
              cx={xAt(i, n)}
              cy={yAt(r.mutation_pct)}
              r={hover === i ? 5 : 3}
              fill="var(--series-2)"
              stroke="var(--surface)"
              strokeWidth={2}
            />
          ),
        )}
        {hover != null && <line className={styles.crosshair} x1={activeX} x2={activeX} y1={PAD.top} y2={HEIGHT - PAD.bottom} />}
        <rect
          x={PAD.left}
          y={PAD.top}
          width={PLOT_W}
          height={PLOT_H}
          className={styles.overlay}
          onPointerMove={handlePointer}
        />
        <text className={styles.axisLabel} x={PAD.left} y={HEIGHT - 6}>
          {formatDate(rows[0].started_at)}
        </text>
        <text className={styles.axisLabel} x={WIDTH - PAD.right} y={HEIGHT - 6} textAnchor="end">
          {formatDate(rows[n - 1].started_at)}
        </text>
      </svg>
      {active && (
        <div className={styles.tooltip} style={{ left: `${(activeX / WIDTH) * 100}%` }}>
          <div className={styles.tooltipDate}>
            {formatDate(active.started_at)} · {active.commit_sha ? active.commit_sha.slice(0, 7) : "no commit"}
          </div>
          <div className={styles.tooltipRow}>
            <span className={styles.tooltipKeyLabel}>
              <span className={styles.tooltipKey} style={{ background: "var(--accent)" }} />
              Coverage
            </span>
            <span className={styles.tooltipValue}>{active.coverage_pct.toFixed(1)}%</span>
          </div>
          <div className={styles.tooltipRow}>
            <span className={styles.tooltipKeyLabel}>
              <span className={styles.tooltipKey} style={{ background: "var(--series-2)" }} />
              Mutation
            </span>
            <span className={styles.tooltipValue}>{active.mutation_pct != null ? `${active.mutation_pct.toFixed(2)}%` : "Not run"}</span>
          </div>
        </div>
      )}
    </div>
  );
}
