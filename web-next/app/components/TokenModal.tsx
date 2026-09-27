"use client";

import { useEffect, useState } from "react";
import styles from "./TokenModal.module.css";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (token: string) => void;
};

export function TokenModal({ isOpen, onClose, onSubmit }: Props) {
  const [val, setVal] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (isOpen && e.key === "Escape") {
        onClose();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  function handleClose() {
    setVal("");
    setError(null);
    onClose();
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!val.trim()) {
      setError("Please provide a valid token to proceed.");
      return;
    }
    const token = val.trim();
    setVal("");
    setError(null);
    onSubmit(token);
  }

  return (
    <div className={styles.overlay} onClick={handleClose} role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <div className={styles.titleArea}>
            <div className={styles.icon} aria-hidden="true">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
            </div>
            <h2 id="modal-title" className={styles.title}>
              Autofix Authorization
            </h2>
          </div>
          <button type="button" className={styles.closeBtn} onClick={handleClose} aria-label="Close dialog">
            &times;
          </button>
        </div>

        <p className={styles.description}>
          AI self-healing test generation runs in a safe server sandbox and requires authorization.
          Once entered, your token is remembered for this session and will not be asked again.
        </p>

        <form onSubmit={handleSubmit} className={styles.inputGroup}>
          <label htmlFor="token-input" className={styles.label}>
            REPOGUARD_FIX_TOKEN
          </label>
          <input
            id="token-input"
            autoFocus
            type="password"
            className={styles.input}
            value={val}
            onChange={(e) => {
              setVal(e.target.value);
              if (error) setError(null);
            }}
            placeholder="Paste your secret server token..."
            autoComplete="off"
            spellCheck={false}
          />
          {error && <span className={styles.error}>{error}</span>}

          <div className={styles.actions}>
            <button type="button" className={styles.cancelBtn} onClick={handleClose}>
              Cancel
            </button>
            <button type="submit" className={styles.confirmBtn}>
              Save & Launch Autofix
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
