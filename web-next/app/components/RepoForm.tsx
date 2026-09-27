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

const DEMO_PATHS = new Set(DEMO_REPOS.map((d) => d.path));
const URL_PATTERN = /^https?:\/\/\S+$/i;

export function RepoForm({ values, onChange, disabled }: Props) {
  const trimmedPath = values.repoPath.trim();
  // The presets above send a server-side filesystem path, not a URL -- they
  // never go through this check. Free-typed input does: this form only
  // validates shape client-side, the backend still just reads a local path.
  const showUrlError = trimmedPath !== "" && !DEMO_PATHS.has(trimmedPath) && !URL_PATTERN.test(trimmedPath);

  return (
    <fieldset className={styles.form} disabled={disabled}>
      <div className={styles.repoRow}>
        <label className={styles.field}>
          <span>Repository URL</span>
          <input
            className={`${styles.input} ${showUrlError ? styles.inputError : ""}`}
            type="text"
            value={values.repoPath}
            onChange={(e) => onChange({ ...values, repoPath: e.target.value })}
            placeholder="https://github.com/usuario/repo"
            spellCheck={false}
            aria-invalid={showUrlError}
          />
          <span className={styles.fieldNote}>El repositorio debe ser un proyecto Python (pytest, Python ≥ 3.10).</span>
          {showUrlError && (
            <span className={styles.fieldError} role="alert">
              Formato incorrecto — debe ser una URL. Ejemplo: https://github.com/usuario/repo
            </span>
          )}
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
            value={values.provider === "watsonx" ? "watsonx" : (values.modelId ?? "gemini-3.8-flash")}
            onChange={(e) => {
              const v = e.target.value;
              if (v === "watsonx") {
                onChange({ ...values, provider: "watsonx", modelId: undefined });
              } else {
                onChange({ ...values, provider: "vertex", modelId: v as "gemini-3.8-flash" | "gemini-3.5-flash" });
              }
            }}
          >
            <option value="gemini-3.8-flash">Google Vertex AI · Gemini 3.8 Flash (Default)</option>
            <option value="gemini-3.5-flash">Google Vertex AI · Gemini 3.5 Flash</option>
            <option value="watsonx">IBM watsonx.ai · Mistral Small 24B / Llama 3.3</option>
          </select>
          <span className={styles.fieldNote}>
            {values.provider === "watsonx"
              ? "Mistral Small 24B / Llama 3.3 (server default)."
              : (values.modelId ?? "gemini-3.8-flash") === "gemini-3.5-flash"
                ? "Gemini 3.5 Flash selected."
                : "Gemini 3.8 Flash active as default."}
          </span>
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
