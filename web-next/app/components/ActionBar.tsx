"use client";

import styles from "./Controls.module.css";

type Props = {
  onAnalyze: () => void;
  onGate: () => void;
  busy: boolean;
};

export function ActionBar({ onAnalyze, onGate, busy }: Props) {
  return (
    <div className={styles.bar}>
      <button type="button" className={`${styles.button} ${styles.primary}`} onClick={onAnalyze} disabled={busy}>
        {busy ? "Analyzing…" : "Analyze"}
      </button>
      <button type="button" className={styles.button} onClick={onGate} disabled={busy}>
        Gate
      </button>
      <button
        type="button"
        className={styles.button}
        disabled
        title="Needs POST /api/fix — PENDING.md Phase 14, gap 3"
      >
        Autofix <span className={styles.soon}>Soon</span>
      </button>
    </div>
  );
}
