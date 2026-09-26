"use client";

import type { StreamEvent } from "../lib/types";

function describe(event: StreamEvent): string {
  switch (event.type) {
    case "start":
      return `Started: ${event.data.repo_path}`;
    case "progress":
      return String(event.data.message ?? event.data.step ?? "");
    case "coverage":
      return `Coverage: ${event.data.percent}% (${event.data.total_lines} lines)`;
    case "gaps":
      return `Gaps: ${(event.data.uncovered_files as string[] | undefined)?.length ?? 0} uncovered files`;
    case "risk":
      return `Risk: ${(event.data.top_files as unknown[] | undefined)?.length ?? 0} files ranked`;
    case "done":
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
  return (
    <ul>
      {events.map((event, i) => (
        <li key={i}>{describe(event)}</li>
      ))}
    </ul>
  );
}
