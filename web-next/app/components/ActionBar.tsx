"use client";

import { Tooltip } from "./Tooltip";
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
      <button
        type="button"
        className={`${styles.button} ${styles.primary}`}
        onClick={onAnalyze}
        disabled={busy}
        title="Runs full suite: coverage, coverage gaps, risk ranking, endpoint smoke tests, and AST mutation testing (if checked)."
      >
        <span>{busy ? "Analyzing…" : "Analyze"}</span>
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
        className={styles.button}
        onClick={onAutofix}
        disabled={busy || !canAutofix}
        title={
          canAutofix
            ? "Autonomously writes missing tests with AI (watsonx or Vertex AI) on a sandbox copy."
            : "Enter the Autofix token above to enable AI test generation"
        }
      >
        <span>Autofix</span>
        <span className={styles.buttonSub}>(Self-Healing AI)</span>
      </button>

      <Tooltip
        content="Analyze runs the full inspection. Gate (Fast) is for fast CI/CD quality checks without the minutes needed for mutation testing. Autofix runs the AI loop to write tests for untested code."
        ariaLabel="Explain actions"
      />
    </div>
  );
}

