"use client";

import { useRef, useState } from "react";
import { RepoForm } from "./components/RepoForm";
import { ActionBar } from "./components/ActionBar";
import { StreamLog } from "./components/StreamLog";
import { StatCards } from "./components/StatCards";
import { GapsList } from "./components/GapsList";
import { RiskTable } from "./components/RiskTable";
import { SummaryPanel } from "./components/SummaryPanel";
import { FixResultPanel } from "./components/FixResultPanel";
import { EndpointsList } from "./components/EndpointsList";
import { Card } from "./components/Card";
import { TokenModal } from "./components/TokenModal";
import styles from "./page.module.css";
import { fetchAnalyze, fetchSummary, streamFix, streamUrl } from "./lib/api";
import type { AnalyzeResponse, FixDone, RepoFormValues, StreamEvent, SummaryResponse } from "./lib/types";

const DEFAULT_VALUES: RepoFormValues = {
  repoPath: "./demo-repo",
  mutation: false,
  gateThreshold: 80,
  provider: "vertex",
};

export default function Home() {
  const [values, setValues] = useState<RepoFormValues>(DEFAULT_VALUES);
  const [busy, setBusy] = useState(false);
  const [autofixing, setAutofixing] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  // Held in memory only: never persisted, never sent anywhere but /api/fix.
  const [token, setToken] = useState("");
  const [fix, setFix] = useState<FixDone | null>(null);
  // The threshold the shown result was measured against, so editing the
  // input afterwards doesn't relabel an old PASS/FAIL.
  const [ranThreshold, setRanThreshold] = useState(DEFAULT_VALUES.gateThreshold);
  // Whether the /api/analyze call in flight runs mutation testing; null when
  // none is in flight. Drives StreamLog's "still measuring" line.
  const [analyzing, setAnalyzing] = useState<{ mutation: boolean } | null>(null);
  const runRef = useRef(0);

  // The summary is fetched here rather than in a SummaryPanel effect because
  // StrictMode runs effects twice in dev, which doubled the paid watsonx.ai call.
  async function loadSummary(data: AnalyzeResponse, run: number, provider?: string, modelId?: string) {
    let next: SummaryResponse;
    try {
      next = await fetchSummary(data, provider, provider === "vertex" ? modelId : undefined);
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

  async function runAnalyze(gateThreshold: number, mutation: boolean) {
    const run = ++runRef.current;
    setRanThreshold(gateThreshold);
    setAnalyzing({ mutation });
    setBusy(true);
    setError(null);
    setEvents([]);
    setResult(null);
    setSummary(null);
    setFix(null);

    const source = new EventSource(streamUrl(values.repoPath, gateThreshold));
    source.onmessage = (msg) => {
      const event = JSON.parse(msg.data) as StreamEvent;
      setEvents((prev) => [...prev, event]);
      if (event.type === "done" || event.type === "error") {
        source.close();
      }
    };
    source.onerror = () => source.close();

    try {
      const data = await fetchAnalyze({ ...values, gateThreshold, mutation });
      setResult(data);
      // Not awaited: the summary must never hold up or fail the dashboard.
      void loadSummary(data, run, values.provider, values.modelId);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setAnalyzing(null);
      setBusy(false);
    }
  }

  async function runAutofix(explicitToken?: string) {
    const activeToken = explicitToken ?? token;
    ++runRef.current;
    setBusy(true);
    setAutofixing(true);
    setError(null);
    setEvents([]);
    setResult(null);
    setSummary(null);
    setFix(null);

    try {
      await streamFix(values, activeToken, (event) => {
        if (event.type === "heartbeat") {
          return;
        }
        setEvents((prev) => [...prev, event]);
        if (event.type === "done") {
          setFix(event.data as unknown as FixDone);
        } else if (event.type === "error") {
          setError(String(event.data.message));
        }
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setAutofixing(false);
      setBusy(false);
    }
  }

  function handleAutofixClick() {
    if (!token.trim()) {
      setModalOpen(true);
      return;
    }
    void runAutofix();
  }

  function handleTokenSubmit(enteredToken: string) {
    setToken(enteredToken);
    setModalOpen(false);
    void runAutofix(enteredToken);
  }

  const streamEnded = events.some((e) => e.type === "done" || e.type === "error");
  const pending =
    analyzing && streamEnded
      ? analyzing.mutation
        ? "Running mutation testing — this can take several minutes"
        : "Finishing the analysis"
      : undefined;

  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <h1 className={styles.title}>TestMind AI</h1>
        <p className={styles.subtitle}>
          Self-Healing Test Suites & Quality Gate for Python · Measures real test effectiveness with AST mutation testing & closes coverage gaps with AI.
        </p>
      </header>
      <Card title="Analyze a repository">
        <RepoForm values={values} onChange={setValues} token={token} onTokenChange={setToken} disabled={busy} />
        <ActionBar
          busy={busy}
          isAnalyzing={analyzing !== null}
          isAutofixing={autofixing}
          onAnalyze={() => runAnalyze(values.gateThreshold, values.mutation)}
          // Like `repoguard gate`: a coverage-only check, never mutation.
          onGate={() => runAnalyze(values.gateThreshold, false)}
          onAutofix={handleAutofixClick}
        />
      </Card>
      {error && (
        <div className={styles.alert} role="alert">
          <div>
            <strong>Error: </strong>
            {error}
          </div>
          {error.toLowerCase().includes("503") && (
            <p style={{ marginTop: "6px", fontSize: "12px", opacity: 0.9 }}>
              Tip: HTTP 503 from Autofix means AI provider credentials (watsonx.ai or Vertex AI) are missing on this server.
            </p>
          )}
          {error.toLowerCase().includes("429") && (
            <p style={{ marginTop: "6px", fontSize: "12px", opacity: 0.9 }}>
              Tip: HTTP 429 means Autofix has hit its rate limit (per-IP or global — each run spends real AI-provider quota). Try again later.
            </p>
          )}
          {error.toLowerCase().includes("409") && (
            <p style={{ marginTop: "6px", fontSize: "12px", opacity: 0.9 }}>
              Tip: HTTP 409 means another Autofix run is already in progress on this server. Wait for it to finish and try again.
            </p>
          )}
        </div>
      )}
      <StreamLog events={events} pending={pending} />
      {fix && <FixResultPanel fix={fix} />}
      {!result && !fix && !busy && !error && events.length === 0 && (
        <p className={styles.empty}>
          Enter a repo path on the backend&rsquo;s machine and press Analyze to measure it.
        </p>
      )}
      {result && (
        <div className={styles.resultSection}>
          <StatCards result={result} gateThreshold={ranThreshold} />
          <div className={styles.columns}>
            <GapsList gaps={result.gaps} />
            <RiskTable risk={result.risk} />
          </div>
          <EndpointsList endpoints={result.endpoints} />
          <SummaryPanel summary={summary} />
        </div>
      )}

      <TokenModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmit={handleTokenSubmit}
      />
    </main>
  );
}

