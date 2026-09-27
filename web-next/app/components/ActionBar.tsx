"use client";

import { Tooltip } from "./Tooltip";
import styles from "./Controls.module.css";

type Props = {
  onAnalyze: () => void;
  onGate: () => void;
  onAutofix: () => void;
  busy: boolean;
  isAnalyzing: boolean;
  isAutofixing: boolean;
};

export function ActionBar({ onAnalyze, onGate, onAutofix, busy, isAnalyzing, isAutofixing }: Props) {
  return (
    <div className={styles.bar}>
      <button
        type="button"
        className={`${styles.button} ${styles.primary} ${isAnalyzing ? styles.analyzingGlow : ""}`}
        onClick={onAnalyze}
        disabled={busy}
        title="Runs full suite: coverage, coverage gaps, risk ranking, endpoint smoke tests, and AST mutation testing (if checked)."
      >
        {isAnalyzing ? (
          <>
            <svg
              className={styles.spinGear}
              viewBox="0 0 24 24"
              width="16"
              height="16"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
            <span>Analyzing…</span>
          </>
        ) : (
          <span>Analyze</span>
        )}
        <span className={styles.buttonSub}>(Full Suite)</span>
      </button>

      <button
        type="button"
        className={styles.button}
        onClick={onGate}
        disabled={busy}
        title="Fast quality check (seconds): measures line coverage and checks against the gate threshold. Skips mutation testing."
      >
        <span>Gate (Fast)</span>
        <span className={styles.buttonSub}>(No Mutation)</span>
      </button>

      <button
        type="button"
        className={`${styles.button} ${isAutofixing ? styles.autofixGlow : ""}`}
        onClick={onAutofix}
        disabled={busy && !isAutofixing}
        title="Autonomously writes missing tests with AI (watsonx or Vertex AI) on a sandbox copy."
      >
        {isAutofixing ? (
          <>
            <svg
              className={styles.spinGear}
              viewBox="0 0 24 24"
              width="15"
              height="15"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
            </svg>
            <span>Healing…</span>
          </>
        ) : (
          <span>Autofix</span>
        )}
        <span className={styles.buttonSub}>(Self-Healing AI)</span>
      </button>

      <Tooltip
        content="Analyze runs the full inspection. Gate (Fast) is for fast CI/CD quality checks without the minutes needed for mutation testing. Autofix runs the AI loop to write tests for untested code."
        ariaLabel="Explain actions"
      />
    </div>
  );
}


