import type { AnalyzeResponse, RepoFormValues, SummaryResponse } from "./types";

function apiBase(): string {
  const base = process.env.NEXT_PUBLIC_REPOGUARD_API_BASE;
  if (!base) {
    throw new Error("NEXT_PUBLIC_REPOGUARD_API_BASE is not set");
  }
  return base;
}

async function request(url: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(url, init);
  } catch {
    // The browser reports "backend down" and "CORS rejected" as the same
    // opaque TypeError ("Failed to fetch"), so the message names both.
    throw new Error(
      `Can't reach the backend at ${apiBase()}. Check that repoguard serve is running there ` +
        `and that its REPOGUARD_CORS_ORIGINS allows ${window.location.origin}.`,
    );
  }
}

async function failure(res: Response, what: string): Promise<Error> {
  try {
    const body = (await res.json()) as { detail?: unknown };
    if (typeof body.detail === "string") {
      return new Error(body.detail);
    }
  } catch {
    // Not a FastAPI JSON error body (e.g. a plain 500 page); fall through.
  }
  return new Error(`${what} failed: ${res.status} ${res.statusText}`);
}

function analyzeParams({ repoPath, mutation, gateThreshold }: RepoFormValues): URLSearchParams {
  return new URLSearchParams({
    repo_path: repoPath,
    mutation: String(mutation),
    gate_threshold: String(gateThreshold),
  });
}

export async function fetchAnalyze(values: RepoFormValues): Promise<AnalyzeResponse> {
  const res = await request(`${apiBase()}/api/analyze?${analyzeParams(values)}`);
  if (!res.ok) {
    throw await failure(res, "analyze");
  }
  return res.json() as Promise<AnalyzeResponse>;
}

export async function fetchSummary(result: AnalyzeResponse): Promise<SummaryResponse> {
  const res = await request(`${apiBase()}/api/summary`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(result),
  });
  if (!res.ok) {
    throw await failure(res, "summary");
  }
  return res.json() as Promise<SummaryResponse>;
}

export function streamUrl(repoPath: string): string {
  return `${apiBase()}/api/stream?${new URLSearchParams({ repo_path: repoPath })}`;
}
