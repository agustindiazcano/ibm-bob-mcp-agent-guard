"use client";

import { useState } from "react";
import { RepoForm } from "./components/RepoForm";
import { ActionBar } from "./components/ActionBar";
import { StreamLog } from "./components/StreamLog";
import { StatCards } from "./components/StatCards";
import { GapsList } from "./components/GapsList";
import { RiskTable } from "./components/RiskTable";
import { fetchAnalyze, streamUrl } from "./lib/api";
import type { AnalyzeResponse, RepoFormValues, StreamEvent } from "./lib/types";

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

  async function runAnalyze(gateThreshold: number) {
    setBusy(true);
    setError(null);
    setEvents([]);
    setResult(null);

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
        </>
      )}
    </main>
  );
}
