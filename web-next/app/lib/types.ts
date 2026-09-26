export type AnalyzeResponse = {
  coverage: { percent: number; covered_lines: number; total_lines: number };
  gaps: { uncovered_files: string[]; missing_lines_by_file: Record<string, number[]> };
  mutation: { score: number; killed: number; survived: number; total: number } | null;
  risk: { file: string; score: number; reasons: string[] }[];
  passed_gate: boolean;
};

export type StreamEventType = "start" | "progress" | "coverage" | "gaps" | "risk" | "done" | "error";

export type StreamEvent = {
  type: StreamEventType;
  data: Record<string, unknown>;
};

export type RepoFormValues = {
  repoPath: string;
  mutation: boolean;
  gateThreshold: number;
};
