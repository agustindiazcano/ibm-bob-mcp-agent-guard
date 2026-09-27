"use client";

import type { RepoFormValues } from "../lib/types";
import { Tooltip } from "./Tooltip";
import styles from "./Controls.module.css";

type Props = {
  values: RepoFormValues;
  onChange: (values: RepoFormValues) => void;
  // Kept out of RepoFormValues so it never lands in /api/analyze's query string.
  token: string;
  onTokenChange: (token: string) => void;
  disabled: boolean;
};

const DEMO_REPOS = [
  { label: "Shop Demo", path: "./demo-repo", desc: "E-commerce API fixture (FastAPI + cart/pricing/inventory)" },
  { label: "Ledger Demo", path: "./eval-fixtures/ledger", desc: "Accounting ledger fixture (core ledger + transactions)" },
];

export function RepoForm({ values, onChange, token, onTokenChange, disabled }: Props) {
  return (
    <fieldset className={styles.form} disabled={disabled}>
      <div className={styles.repoRow}>
        <label className={styles.field}>
          <span>
            Repo path on server
            <Tooltip
              content="Absolute or relative path to a Python project on the server machine containing pytest tests."
              ariaLabel="About repo path"
            />
          </span>
          <input
            className={styles.input}
            type="text"
            value={values.repoPath}
            onChange={(e) => onChange({ ...values, repoPath: e.target.value })}
            placeholder="./demo-repo"
            spellCheck={false}
          />
        </label>
        <div className={styles.presetsBar}>
          <span>Quick select demo:</span>
          {DEMO_REPOS.map((demo) => (
            <button
              key={demo.path}
              type="button"
              className={`${styles.presetBtn} ${values.repoPath === demo.path ? styles.presetBtnActive : ""}`}
              onClick={() => onChange({ ...values, repoPath: demo.path })}
              title={demo.desc}
            >
              {demo.label}
            </button>
          ))}
        </div>
      </div>

      <div className={styles.controlsRow}>
        <label className={styles.field}>
          <span>
            Gate threshold (%)
            <Tooltip
              content="Target line coverage required to PASS the quality gate. Used by CI/CD pipelines to block weak commits."
              ariaLabel="About gate threshold"
            />
          </span>
          <input
            className={styles.input}
            type="number"
            min={0}
            max={100}
            value={values.gateThreshold}
            onChange={(e) => onChange({ ...values, gateThreshold: Number(e.target.value) })}
          />
          <span className={styles.fieldNote}>Target coverage for PASS/FAIL</span>
        </label>

        <label className={styles.field}>
          <span>
            Autofix token
            <Tooltip
              content="Requires backend REPOGUARD_FIX_TOKEN + AI provider (watsonx or Vertex AI). Tests are written in an isolated sandbox, never in source code."
              ariaLabel="About Autofix token"
            />
          </span>
          <input
            className={styles.input}
            type="password"
            value={token}
            onChange={(e) => onTokenChange(e.target.value)}
            placeholder="Set on server: REPOGUARD_FIX_TOKEN"
            autoComplete="off"
          />
          <span className={styles.fieldNote}>Enables AI self-healing test generation</span>
        </label>

        <label className={styles.check}>
          <input
            type="checkbox"
            checked={values.mutation}
            onChange={(e) => onChange({ ...values, mutation: e.target.checked })}
          />
          <span>
            Run mutation testing
            <Tooltip
              content="Injects AST mutants (operator flips, constant swaps) to measure if tests actually detect bugs. Takes 1–3 minutes."
              ariaLabel="About mutation testing"
            />
          </span>
        </label>
      </div>

      <div className={styles.infoBanner}>
        <strong>Target Environment & Scope:</strong> Supports Python ≥ 3.10 with <code>pytest</code> and optional FastAPI endpoint inspection. Best suited for focused microservices, packages, or modules. For large codebases, run <strong>Gate (Fast)</strong> or keep mutation testing unchecked to avoid long execution times.
      </div>
    </fieldset>
  );
}

