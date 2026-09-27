"use client";

import type { RepoFormValues } from "../lib/types";
import { Tooltip } from "./Tooltip";
import styles from "./Controls.module.css";

type Props = {
  values: RepoFormValues;
  onChange: (values: RepoFormValues) => void;
  disabled: boolean;
};

const DEMO_REPOS = [
  { label: "Shop Demo", path: "./demo-repo", desc: "E-commerce API fixture (FastAPI + cart/pricing/inventory)" },
  { label: "Ledger Demo", path: "./eval-fixtures/ledger", desc: "Accounting ledger fixture (core ledger + transactions)" },
];

export function RepoForm({ values, onChange, disabled }: Props) {
  return (
    <fieldset className={styles.form} disabled={disabled}>
      <div className={styles.repoRow}>
        <label className={styles.field}>
          <span>
            Repo path on server
            <Tooltip
              content="Path to a Python project on the server machine containing pytest tests (Python ≥ 3.10, FastAPI endpoint inspection supported)."
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

        <div className={`${styles.field} ${styles.providerField}`}>
          <span>
            Multicloud AI Provider & Model
            <Tooltip
              content="Choose which cloud AI provider and LLM powers narrative summaries and the self-healing fix loop. Google Vertex AI runs Gemini Flash 3.8 / 3.5 (global endpoint). IBM watsonx runs Mistral/Llama."
              ariaLabel="About AI providers"
            />
          </span>
          <select
            className={styles.select}
            value={values.provider ?? "vertex"}
            onChange={(e) => onChange({ ...values, provider: e.target.value as "vertex" | "watsonx" })}
          >
            <option value="vertex">Google Vertex AI · Gemini 3.8 Flash (Default)</option>
            <option value="vertex">Google Vertex AI · Gemini 3.5 Flash</option>
            <option value="watsonx">IBM watsonx.ai · Mistral Small 24B / Llama 3.3</option>
          </select>
          <span className={styles.fieldNote}>Gemini 3.8 Flash active as default.</span>
        </div>

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
    </fieldset>
  );
}
