import type { AnalyzeResponse, RepoFormValues, StreamEvent, SummaryResponse } from "./types";

export function apiBase(): string {
  const base = process.env.NEXT_PUBLIC_REPOGUARD_API_BASE;
  if (!base) {
    throw new Error("NEXT_PUBLIC_REPOGUARD_API_BASE is not set");
  }
  return base;
}

export async function request(url: string, init?: RequestInit): Promise<Response> {
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

export async function failure(res: Response, what: string): Promise<Error> {
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

// gate_threshold must match /api/analyze's, or the stream's `done` line
// reports a different PASS/FAIL than the stat cards.
export function streamUrl(repoPath: string, gateThreshold: number): string {
  const params = new URLSearchParams({ repo_path: repoPath, gate_threshold: String(gateThreshold) });
  return `${apiBase()}/api/stream?${params}`;
}

// POST /api/fix streams NDJSON (one event per line) for several minutes, so
// it's read incrementally here instead of awaited as one JSON body.
// EventSource can't send a POST body or an Authorization header.
export async function streamFix(
  { repoPath, gateThreshold }: RepoFormValues,
  token: string,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const res = await request(`${apiBase()}/api/fix`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ repo_path: repoPath, gate_threshold: gateThreshold }),
  });
  if (!res.ok || !res.body) {
    throw await failure(res, "autofix");
  }
  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffered = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    buffered += value;
    const lines = buffered.split("\n");
    buffered = lines.pop() ?? "";
    for (const line of lines) {
      if (line.trim()) {
        onEvent(JSON.parse(line) as StreamEvent);
      }
    }
  }
  if (buffered.trim()) {
    onEvent(JSON.parse(buffered) as StreamEvent);
  }
}
