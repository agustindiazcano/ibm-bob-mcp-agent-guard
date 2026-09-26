export type AnalyzeResponse = {
  coverage: { percent: number; covered_lines: number; total_lines: number };
  gaps: { uncovered_files: string[]; missing_lines_by_file: Record<string, number[]> };
  mutation: { score: number; killed: number; survived: number; total: number } | null;
  risk: { file: string; score: number; reasons: string[] }[];
  passed_gate: boolean;
};

export type SummaryResponse = {
  ok: boolean;
  text: string;
  error: string;
  provider: string;
};

export type StreamEventType =
  | "start"
  | "progress"
  | "coverage"
  | "gaps"
  | "risk"
  | "done"
  | "error"
  // POST /api/fix only (web/fix_job.py, orchestrator.run_fix_loop's on_event)
  | "baseline_start"
  | "baseline_done"
  | "writer_start"
  | "critic_start"
  | "remeasure_start"
  | "remeasure_done"
  | "heartbeat";

export type StreamEvent = {
  type: StreamEventType;
  data: Record<string, unknown>;
};

export type RepoFormValues = {
  repoPath: string;
  mutation: boolean;
  gateThreshold: number;
};

export type Dashboard = Omit<AnalyzeResponse, "passed_gate">;

export type FixFile = {
  path: string;
  status: "added" | "modified";
  content: string;
};

// The `done` event's data from POST /api/fix. `before`/`after` are the
// engine's own dashboards; `critic_notes` are advisory model output.
export type FixDone = {
  provider: string;
  before: Dashboard;
  after: Dashboard | null;
  files_attempted: string[];
  files: FixFile[];
  critic_notes: string[];
  evidence: string;
};
