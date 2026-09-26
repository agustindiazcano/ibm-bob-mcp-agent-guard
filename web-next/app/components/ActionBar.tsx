"use client";

import styles from "./Controls.module.css";

type Props = {
  onAnalyze: () => void;
  onGate: () => void;
  onAutofix: () => void;
  busy: boolean;
  canAutofix: boolean;
};

export function ActionBar({ onAnalyze, onGate, onAutofix, busy, canAutofix }: Props) {
  return (
    <div className={styles.bar}>
      <button type="button" className={`${styles.button} ${styles.primary}`} onClick={onAnalyze} disabled={busy}>
        {busy ? "Analyzing…" : "Analyze"}
      </button>
      <button
        type="button"
        className={styles.button}
        onClick={onGate}
        disabled={busy}
        title="Coverage-only check against the threshold, like repoguard gate — skips mutation testing"
      >
        Gate
      </button>
      <button
        type="button"
        className={styles.button}
        onClick={onAutofix}
        disabled={busy || !canAutofix}
        title={canAutofix ? "Write missing tests with AI, on a copy of the repo" : "Enter the Autofix token first"}
      >
        Autofix
      </button>
    </div>
  );
}
