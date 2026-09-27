"use client";

import { useMemo, useState } from "react";
import type { Dashboard, FixDone } from "../lib/types";
import { CodeViewer } from "./CodeViewer";
import { CriticReviewCard } from "./CriticReviewCard";
import styles from "./FixResultPanel.module.css";

function mutationText(d: Dashboard | null): string {
  if (!d?.mutation) {
    return "not measured";
  }
  return `${d.mutation.score.toFixed(2)}% (${d.mutation.killed}/${d.mutation.total})`;
}

function coverageText(d: Dashboard | null): string {
  return d ? `${d.coverage.percent.toFixed(1)}%` : "not measured";
}

// Splits combined raw critic notes if they contain multiple target file blocks
function normalizeCriticNotes(notes: string[]): string[] {
  const normalized: string[] = [];

  for (const raw of notes) {
    if (!raw) continue;
    // Check if the raw text contains multiple file markers like "\nshop/api.py:"
    const splitRegex = /\n(?=[a-zA-Z0-9_\-./]+\.py:)/g;
    const parts = raw.split(splitRegex);
    for (const part of parts) {
      const trimmed = part.trim();
      if (trimmed) {
        normalized.push(trimmed);
      }
    }
  }

  return normalized;
}

export function FixResultPanel({ fix }: { fix: FixDone }) {
  const [activeTab, setActiveTab] = useState<"tests" | "critic" | "evidence">("tests");

  const normalizedNotes = useMemo(() => {
    return normalizeCriticNotes(fix.critic_notes || []);
  }, [fix.critic_notes]);

  const mutationDelta = useMemo(() => {
    if (!fix.before?.mutation || !fix.after?.mutation) return null;
    return fix.after.mutation.score - fix.before.mutation.score;
  }, [fix.before, fix.after]);

  const coverageDelta = useMemo(() => {
    if (!fix.before?.coverage || !fix.after?.coverage) return null;
    return fix.after.coverage.percent - fix.before.coverage.percent;
  }, [fix.before, fix.after]);

  return (
    <div className={styles.panel}>
      <section className={styles.heroCard} aria-label="Autofix Healing Results">
        <div className={styles.heroHeader}>
          <div className={styles.heroTitle}>
            <span className={styles.heroIcon}>⚡</span>
            <span>Self-Healing Autofix Completed</span>
          </div>
          <div className={styles.badges}>
            <span className={styles.providerBadge}>
              <span>🤖</span>
              <span>via {fix.provider}</span>
            </span>
            <span className={styles.filesCountBadge}>
              <span>📦</span>
              <span>{fix.files.length} test file{fix.files.length === 1 ? "" : "s"} generated</span>
            </span>
          </div>
        </div>

        <div className={styles.metricsGrid}>
          <div className={styles.metricCard}>
            <div className={styles.metricLabel}>
              <span>🎯</span>
              <span>Mutation Score (Defect Detection)</span>
            </div>
            <div className={styles.metricComparison}>
              <span className={styles.metricBefore}>{mutationText(fix.before)}</span>
              <span className={styles.arrow} aria-hidden>→</span>
              <strong className={styles.metricAfter}>{mutationText(fix.after)}</strong>
              {mutationDelta !== null && (
                <span className={styles.deltaBadge}>
                  {mutationDelta >= 0 ? `+${mutationDelta.toFixed(2)}%` : `${mutationDelta.toFixed(2)}%`}
                </span>
              )}
            </div>
          </div>

          <div className={styles.metricCard}>
            <div className={styles.metricLabel}>
              <span>📊</span>
              <span>Line Coverage</span>
            </div>
            <div className={styles.metricComparison}>
              <span className={styles.metricBefore}>{coverageText(fix.before)}</span>
              <span className={styles.arrow} aria-hidden>→</span>
              <strong className={styles.metricAfter}>{coverageText(fix.after)}</strong>
              {coverageDelta !== null && (
                <span className={styles.deltaBadge}>
                  {coverageDelta >= 0 ? `+${coverageDelta.toFixed(1)}%` : `${coverageDelta.toFixed(1)}%`}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className={styles.heroNotice}>
          <span>💡</span>
          <div>
            <strong>Isolated Sandbox Execution: </strong>
            Tests were generated, evaluated by the AI Critic, and executed in an isolated server sandbox.
            Nothing was committed to your repository. Copy the verified tests below into your repo&rsquo;s <code>tests/</code> folder.
          </div>
        </div>
      </section>

      {/* Tabs */}
      <div className={styles.tabsNav} role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "tests"}
          className={`${styles.tabButton} ${activeTab === "tests" ? styles.tabButtonActive : ""}`}
          onClick={() => setActiveTab("tests")}
        >
          <span>💻</span>
          <span>Generated Tests</span>
          <span className={styles.tabCount}>{fix.files.length}</span>
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "critic"}
          className={`${styles.tabButton} ${activeTab === "critic" ? styles.tabButtonActive : ""}`}
          onClick={() => setActiveTab("critic")}
        >
          <span>🛡️</span>
          <span>Critic Reviews & Quality Gates</span>
          <span className={styles.tabCount}>{normalizedNotes.length}</span>
        </button>

        {fix.evidence && (
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "evidence"}
            className={`${styles.tabButton} ${activeTab === "evidence" ? styles.tabButtonActive : ""}`}
            onClick={() => setActiveTab("evidence")}
          >
            <span>📋</span>
            <span>Audit & Verification Evidence</span>
          </button>
        )}
      </div>

      {/* Tab Panels */}
      {activeTab === "tests" && (
        <div>
          {fix.files.length === 0 ? (
            <div className={styles.emptyState}>
              <p>No test files were generated or accepted during this fix cycle.</p>
            </div>
          ) : (
            <CodeViewer files={fix.files} />
          )}
        </div>
      )}

      {activeTab === "critic" && (
        <div>
          {normalizedNotes.length === 0 ? (
            <div className={styles.emptyState}>
              <p>No critic reviews available for this run.</p>
            </div>
          ) : (
            <div>
              {normalizedNotes.map((note, idx) => (
                <CriticReviewCard key={idx} note={note} />
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === "evidence" && fix.evidence && (
        <div className={styles.evidenceArea}>
          {fix.evidence}
        </div>
      )}
    </div>
  );
}
