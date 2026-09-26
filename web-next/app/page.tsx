"use client";

import { useRef, useState } from "react";
import { RepoForm } from "./components/RepoForm";
import { ActionBar } from "./components/ActionBar";
import { StreamLog } from "./components/StreamLog";
import { StatCards } from "./components/StatCards";
import { GapsList } from "./components/GapsList";
import { RiskTable } from "./components/RiskTable";
import { SummaryPanel } from "./components/SummaryPanel";
import { fetchAnalyze, fetchSummary, streamUrl } from "./lib/api";
import type { AnalyzeResponse, RepoFormValues, StreamEvent, SummaryResponse } from "./lib/types";

const DEFAULT_VALUES: RepoFormValues = {
  repoPath: "./demo-repo",
  mutation: false,
  gateThreshold: 80,
};

export default function Home() {
  const [values, setValues] = useState<RepoFormValues>(DEFAULT_VALUES);
  const [busy, setBusy] = useState(false);
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const runRef = useRef(0);

  // The summary is fetched here rather than in a SummaryPanel effect because
  // StrictMode runs effects twice in dev, which doubled the paid watsonx.ai call.
  async function loadSummary(data: AnalyzeResponse, run: number) {
    let next: SummaryResponse;
    try {
      next = await fetchSummary(data);
    } catch (err) {
      next = {
        ok: false,
        text: "",
        error: err instanceof Error ? err.message : String(err),
        provider: "",
      };
    }
    if (runRef.current === run) {
      setSummary(next);
    }
  }

  async function runAnalyze(gateThreshold: number) {
    const run = ++runRef.current;
    setBusy(true);
    setError(null);
    setEvents([]);
    setResult(null);
    setSummary(null);

    const source = new EventSource(streamUrl(values.repoPath));
    source.onmessage = (msg) => {
      const event = JSON.parse(msg.data) as StreamEvent;
      setEvents((prev) => [...prev, event]);
      if (event.type === "done" || event.type === "error") {
        source.close();
      }
    };
    source.onerror = () => source.close();

    try {
      const data = await fetchAnalyze({ ...values, gateThreshold });
      setResult(data);
      // Not awaited: the summary must never hold up or fail the dashboard.
      void loadSummary(data, run);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <h1>TestMind AI</h1>
      <RepoForm values={values} onChange={setValues} disabled={busy} />
      <ActionBar
        busy={busy}
        onAnalyze={() => runAnalyze(values.gateThreshold)}
        onGate={() => runAnalyze(values.gateThreshold)}
      />
      {error && <p role="alert">{error}</p>}
      <StreamLog events={events} />
      {result && (
        <>
          <StatCards result={result} />
          <GapsList gaps={result.gaps} />
          <RiskTable risk={result.risk} />
          <SummaryPanel summary={summary} />
        </>
      )}
    </main>
  );
}
