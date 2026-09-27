import type { Metadata } from "next";
import { ButtonLink, PageHeader, PageShell, Section, Tag } from "../components/site/Page";
import { Icon } from "../components/site/Icon";
import blocks from "../components/site/Blocks.module.css";
import styles from "./mutation.module.css";

export const metadata: Metadata = {
  title: "AST Mutation Engine",
  description: "TestMind AI's built-in AST mutation testing engine: deterministic, zero external dependencies, verifiable bug injection.",
};

const OPERATORS = [
  {
    name: "Comparison Inversion",
    original: "if quantity > max_stock:",
    mutated: "if quantity >= max_stock:",
    category: "Boundary Conditions",
    killedRate: "92%",
  },
  {
    name: "Arithmetic Operator Swap",
    original: "total = price * quantity",
    mutated: "total = price + quantity",
    category: "Calculation Errors",
    killedRate: "88%",
  },
  {
    name: "Boolean Logic Inversion",
    original: "if is_vip and has_coupon:",
    mutated: "if is_vip or has_coupon:",
    category: "Conditional Logic",
    killedRate: "85%",
  },
  {
    name: "Exception Elimination",
    original: "raise OutOfStockError(item_id)",
    mutated: "pass # dropped exception",
    category: "Error Handling",
    killedRate: "95%",
  },
];

export default function MutationEnginePage() {
  return (
    <PageShell>
      <PageHeader
        eyebrow="Slide 07 · Engine"
        title="Deterministic AST Mutation Testing Engine"
        lead="Coverage only verifies lines were executed, not whether tests catch real bugs. TestMind AI generates deterministic mutants by parsing Python source with stdlib ast, validating the unmutated baseline before scoring."
        actions={
          <>
            <ButtonLink href="/swarm" variant="secondary">
              ← Slide 06: Swarm
            </ButtonLink>
            <ButtonLink href="/multicloud" variant="primary">
              Next Slide: Multicloud AI →
            </ButtonLink>
          </>
        }
      />

      <Section
        title="Core Mutation Operators"
        intro="The engine introduces subtle, realistic bugs across AST nodes to systematically evaluate test suite sensitivity."
      >
        <div className={styles.operatorGrid}>
          {OPERATORS.map((op) => (
            <div key={op.name} className={styles.opCard}>
              <div className={styles.opHead}>
                <span className={styles.opName}>{op.name}</span>
                <Tag tone="live">{op.category}</Tag>
              </div>

              <div className={styles.codeDiff}>
                <div className={styles.codeRow}>
                  <span className={styles.diffMinus}>-</span>
                  <code>{op.original}</code>
                </div>
                <div className={styles.codeRow}>
                  <span className={styles.diffPlus}>+</span>
                  <code>{op.mutated}</code>
                </div>
              </div>

              <div className={styles.opFooter}>
                <span className={styles.killLabel}>Killed by AI Suite:</span>
                <span className={styles.killValue}>{op.killedRate}</span>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section
        title="Determinism Guarantees"
        intro="Determinism is non-negotiable in QA tooling: same repository in, exact same numbers out."
      >
        <div className={blocks.grid}>
          <div className={blocks.item}>
            <div className={blocks.itemHead}>
              <Icon name="check" />
              <h3>Unmutated Baseline Assertion</h3>
            </div>
            <p>
              The engine executes the suite against unmutated code first. If the baseline fails, mutation testing halts
              immediately to prevent false 100% kill-rate illusions.
            </p>
          </div>

          <div className={blocks.item}>
            <div className={blocks.itemHead}>
              <Icon name="bug" />
              <h3>Bytecode Cache Isolation</h3>
            </div>
            <p>
              Every mutant execution runs with <code>PYTHONDONTWRITEBYTECODE=1</code> and <code>sys.executable</code> to
              prevent stale <code>.pyc</code> artifacts or host PATH hijacking.
            </p>
          </div>

          <div className={blocks.item}>
            <div className={blocks.itemHead}>
              <Icon name="trend" />
              <h3>Direct AST Manipulation</h3>
            </div>
            <p>
              No external tools (mutmut, Stryker). Written directly on Python&apos;s standard library <code>ast</code> for
              instant start times and predictable AST traversal.
            </p>
          </div>
        </div>
      </Section>
    </PageShell>
  );
}
