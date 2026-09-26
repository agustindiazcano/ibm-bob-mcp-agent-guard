"use client";

import type { StreamEvent } from "../lib/types";
import { Card } from "./Card";
import styles from "./StreamLog.module.css";

function describe(event: StreamEvent): string {
  switch (event.type) {
    case "start":
      return `Started: ${event.data.repo_path}`;
    case "progress":
      return String(event.data.message ?? event.data.step ?? "");
    case "coverage":
      // Same 1-decimal display as StatCards; the raw value is unchanged.
      return `Coverage: ${Number(event.data.percent).toFixed(1)}% (${event.data.total_lines} lines)`;
    case "gaps":
      return `Gaps: ${(event.data.uncovered_files as string[] | undefined)?.length ?? 0} uncovered files`;
    case "risk":
      return `Risk: ${(event.data.top_files as unknown[] | undefined)?.length ?? 0} files ranked`;
    case "baseline_start":
      return "Measuring baseline (coverage, mutation, endpoints)…";
    case "baseline_done":
      return `Baseline measured — targeting ${(event.data.files as string[] | undefined)?.join(", ") || "no files"}`;
    case "writer_start":
      return `Writing tests for ${event.data.file}…`;
    case "critic_start":
      return `Critic reviewing tests for ${event.data.file}…`;
    case "remeasure_start":
      return "Re-measuring with the new tests…";
    case "remeasure_done":
      return `Re-measured — passed_gate: ${event.data.passed_gate}`;
    case "done":
      if (Array.isArray(event.data.files)) {
        return `Done — ${event.data.files.length} test file(s) written`;
      }
      return `Done — passed_gate: ${event.data.passed_gate}`;
    case "error":
      return `Error: ${event.data.message}`;
    default:
      return JSON.stringify(event.data);
  }
}

export function StreamLog({ events }: { events: StreamEvent[] }) {
  if (events.length === 0) {
    return null;
  }
  const last = events[events.length - 1].type;
  const finished = last === "done" || last === "error";
  const status = last === "error" ? (
    <span className={`${styles.status} ${styles.statusError}`}>Error</span>
  ) : last === "done" ? (
    <span className={`${styles.status} ${styles.statusDone}`}>Done</span>
  ) : (
    <span className={styles.status}>Running</span>
  );

  return (
    <Card title="Live progress" aside={status}>
      <ul className={styles.list} aria-live="polite">
        {events.map((event, i) => {
          const active = !finished && i === events.length - 1;
          const className = [
            styles.item,
            active ? styles.active : "",
            event.type === "error" ? styles.error : "",
          ].join(" ");
          return (
            <li key={i} className={className}>
              <span className={styles.dot} aria-hidden />
              {describe(event)}
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
