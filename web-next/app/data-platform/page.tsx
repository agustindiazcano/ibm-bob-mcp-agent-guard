import type { Metadata } from "next";
import { ButtonLink, PageHeader, PageShell, Section, Tag } from "../components/site/Page";
import { Icon } from "../components/site/Icon";
import blocks from "../components/site/Blocks.module.css";
import styles from "./data.module.css";

export const metadata: Metadata = {
  title: "Data Platform",
  description: "Phase 17 Data Platform: SQLAlchemy 2 Core, PostgreSQL 16, portable view DDL, and historical test analytics.",
};

const ANALYTICAL_VIEWS = [
  {
    name: "v_passed_gate",
    description: "Evaluates quality gate compliance over time without duplicating business logic in application code.",
    queryTarget: "Gate pass/fail trends across branches",
  },
  {
    name: "v_trends",
    description: "Tracks coverage vs. mutation score deltas per commit to verify real bug-catching improvements.",
    queryTarget: "Quality trajectory & regression alerts",
  },
  {
    name: "v_survival_by_operator",
    description: "Aggregates surviving mutants by AST operator kind (comparisons, arithmetic, exception elimination).",
    queryTarget: "Blind-spot discovery across the codebase",
  },
  {
    name: "v_persistent_survivors",
    description: "Identifies mutants that survive multiple consecutive runs across multiple git revisions.",
    queryTarget: "Hardened equivalent mutant detection",
  },
  {
    name: "v_flaky_tests",
    description: "Detects tests whose pass/fail status oscillates without code changes between identical commits.",
    queryTarget: "Test flakiness eradication",
  },
];

export default function DataPlatformPage() {
  return (
    <PageShell>
      <PageHeader
        eyebrow="Slide 10 · Platform"
        title="PostgreSQL Run History & Analytics Platform"
        lead="Phase 17 enterprise data platform: stores exact, unrounded run metrics in Cloud SQL PostgreSQL 16 via SQLAlchemy 2 Core. Derived metrics and trend analytics live entirely in portable SQL views."
        actions={
          <>
            <ButtonLink href="/security-gate" variant="secondary">
              ← Slide 09: Enterprise Security
            </ButtonLink>
            <ButtonLink href="/" variant="primary">
              Return to Slide 01: Analyze →
            </ButtonLink>
          </>
        }
      />

      <Section
        title="Portable Analytical Views"
        intro="Derived values live only in view DDL, never hardcoded in application logic. PostgreSQL and SQLite share identical view semantics."
      >
        <div className={styles.viewsGrid}>
          {ANALYTICAL_VIEWS.map((view) => (
            <div key={view.name} className={styles.viewCard}>
              <div className={styles.viewHead}>
                <code className={styles.viewName}>{view.name}</code>
                <Tag tone="live">SQL View</Tag>
              </div>
              <p className={styles.viewDesc}>{view.description}</p>
              <div className={styles.viewTarget}>
                <span className={styles.targetLabel}>Target Insight:</span>
                <span className={styles.targetVal}>{view.queryTarget}</span>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section
        title="Data Ingestion & Integrity Principles"
        intro="The data platform adheres to strict data integrity rules defined in docs/DATA_PLATFORM.md."
      >
        <div className={blocks.grid}>
          <div className={blocks.item}>
            <div className={blocks.itemHead}>
              <Icon name="check" />
              <h3>Unrounded Double Precision</h3>
            </div>
            <p>
              Metrics like coverage (e.g. <code>60.264900662251655%</code>) are stored as 64-bit IEEE floating point
              numbers, preventing precision drift in downstream assertions.
            </p>
          </div>

          <div className={blocks.item}>
            <div className={blocks.itemHead}>
              <Icon name="terminal" />
              <h3>Token-Authenticated Push</h3>
            </div>
            <p>
              CI runners push results via <code>repoguard analyze --push</code>. Ingestion requires per-project tokens;
              arbitrary clients cannot pollute the historical database.
            </p>
          </div>

          <div className={blocks.item}>
            <div className={blocks.itemHead}>
              <Icon name="trend" />
              <h3>Fail-Fast Connectivity Probe</h3>
            </div>
            <p>
              When persistence is requested, the store connection is validated before the test suite begins. A database
              misconfiguration fails in milliseconds, never after 10 minutes of mutation runs.
            </p>
          </div>
        </div>
      </Section>
    </PageShell>
  );
}
