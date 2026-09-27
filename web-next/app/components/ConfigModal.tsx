"use client";

import { useEffect, useState } from "react";
import { useConfig } from "../context/ConfigContext";
import styles from "./ConfigModal.module.css";

function ConfigDialog({
  analyzeToken,
  autofixToken,
  onSave,
  onClose,
}: {
  analyzeToken: string;
  autofixToken: string;
  onSave: (analyze: string, autofix: string) => void;
  onClose: () => void;
}) {
  const [localAnalyze, setLocalAnalyze] = useState(analyzeToken);
  const [localAutofix, setLocalAutofix] = useState(autofixToken);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        onClose();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  function handleFormSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSave(localAnalyze.trim(), localAutofix.trim());
    setSaved(true);
    setTimeout(() => {
      setSaved(false);
      onClose();
    }, 400);
  }

  return (
    <div className={styles.overlay} onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="config-title">
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <div className={styles.titleArea}>
            <div className={styles.icon} aria-hidden="true">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>
            </div>
            <h2 id="config-title" className={styles.title}>
              Server Configuration & Tokens
            </h2>
          </div>
          <button type="button" className={styles.closeBtn} onClick={onClose} aria-label="Close dialog">
            &times;
          </button>
        </div>

        <form onSubmit={handleFormSubmit} className={styles.body}>
          <div className={styles.field}>
            <label htmlFor="autofix-token" className={styles.label}>
              <span>Autofix Token (REPOGUARD_FIX_TOKEN)</span>
            </label>
            <input
              id="autofix-token"
              type="password"
              className={styles.input}
              value={localAutofix}
              onChange={(e) => setLocalAutofix(e.target.value)}
              placeholder="Bearer token for self-healing AI test generation"
              autoComplete="off"
            />
            <span className={styles.hint}>
              Required by <code>POST /api/fix</code> to autonomously generate and verify missing tests.
            </span>
          </div>

          <div className={styles.field}>
            <label htmlFor="analyze-token" className={styles.label}>
              <span>Analyze / Project Token (REPOGUARD_PROJECT_TOKEN)</span>
            </label>
            <input
              id="analyze-token"
              type="password"
              className={styles.input}
              value={localAnalyze}
              onChange={(e) => setLocalAnalyze(e.target.value)}
              placeholder="Bearer token for storing runs into database"
              autoComplete="off"
            />
            <span className={styles.hint}>
              Required by <code>POST /api/runs</code> to ingest and persist test runs into Cloud SQL / PostgreSQL.
            </span>
          </div>

          <div className={styles.infoBox}>
            <strong>Cloud AI Credentials:</strong> Google Vertex AI (Gemini) or IBM watsonx.ai keys are configured directly in your server&rsquo;s environment variables. Tokens entered here are stored locally in your browser.
          </div>

          <div className={styles.footer}>
            {saved && (
              <span className={styles.savedMsg}>
                ✓ Saved successfully!
              </span>
            )}
            <button type="submit" className={styles.saveBtn}>
              Save & Apply
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function ConfigModal() {
  const {
    analyzeToken,
    autofixToken,
    setAnalyzeToken,
    setAutofixToken,
    isConfigOpen,
    closeConfig,
  } = useConfig();

  if (!isConfigOpen) return null;

  return (
    <ConfigDialog
      analyzeToken={analyzeToken}
      autofixToken={autofixToken}
      onSave={(analyze, autofix) => {
        setAnalyzeToken(analyze);
        setAutofixToken(autofix);
      }}
      onClose={closeConfig}
    />
  );
}
