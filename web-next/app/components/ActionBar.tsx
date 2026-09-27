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
  swarm?: boolean;
  onToggleSwarm?: () => void;
};

export function ActionBar({
  onAnalyze,
  onGate,
  onAutofix,
  busy,
  isAnalyzing,
  isAutofixing,
  swarm = true,
  onToggleSwarm,
}: Props) {
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
      </button>

      <button
        type="button"
        className={styles.button}
        onClick={onGate}
        disabled={busy}
        title="Quality Gate rápido (segundos): mide cobertura de líneas y verifica si supera el umbral (PASS/FAIL). Omite las mutaciones AST para dar feedback inmediato en CI/CD."
      >
        <span>Gate</span>
      </button>

      <button
        type="button"
        className={`${styles.button} ${styles.autofixBtn} ${isAutofixing ? styles.autofixGlow : ""}`}
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
      </button>

      <div className={styles.swarmGroup}>
        <label
          className={`${styles.swarmControl} ${swarm ? styles.swarmOn : ""}`}
          title="Multi-agent swarm: Accelerates testing speed by parallelizing tasks across multiple agents simultaneously in isolated sandboxes."
        >
          <input
            type="checkbox"
            className={styles.swarmInput}
            checked={swarm}
            onChange={onToggleSwarm}
            disabled={busy}
          />
          <span className={styles.swarmSlider} />
          <span className={styles.swarmText}>Multi-agent swarm</span>
          <span className={styles.cloudBadge} aria-hidden="true">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4C9.11 4 6.6 5.64 5.35 8.04C2.34 8.36 0 10.91 0 14C0 17.31 2.69 20 6 20H19C21.76 20 24 17.76 24 15C24 12.36 21.95 10.22 19.35 10.04Z" />
            </svg>
          </span>
        </label>
        <Tooltip
          content="Accelerates test generation and healing by parallelizing tasks across multiple agents simultaneously in isolated sandboxes."
          ariaLabel="About Multi-agent swarm"
        />
      </div>
    </div>
  );
}
