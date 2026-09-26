import type { AnalyzeResponse, RepoFormValues, SummaryResponse } from "./types";

function apiBase(): string {
  const base = process.env.NEXT_PUBLIC_REPOGUARD_API_BASE;
  if (!base) {
    throw new Error("NEXT_PUBLIC_REPOGUARD_API_BASE is not set");
  }
  return base;
}

function analyzeParams({ repoPath, mutation, gateThreshold }: RepoFormValues): URLSearchParams {
  return new URLSearchParams({
    repo_path: repoPath,
    mutation: String(mutation),
    gate_threshold: String(gateThreshold),
  });
}

export async function fetchAnalyze(values: RepoFormValues): Promise<AnalyzeResponse> {
  const res = await fetch(`${apiBase()}/api/analyze?${analyzeParams(values)}`);
  if (!res.ok) {
    throw new Error(`analyze failed: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<AnalyzeResponse>;
}

export async function fetchSummary(result: AnalyzeResponse): Promise<SummaryResponse> {
  const res = await fetch(`${apiBase()}/api/summary`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(result),
  });
  if (!res.ok) {
    throw new Error(`summary failed: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<SummaryResponse>;
}

export function streamUrl(repoPath: string): string {
  return `${apiBase()}/api/stream?${new URLSearchParams({ repo_path: repoPath })}`;
}
