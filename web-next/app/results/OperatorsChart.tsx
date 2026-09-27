import type { OperatorRow } from "./history";
import { Card } from "../components/Card";
import styles from "../components/Lists.module.css";

// Survival by mutation operator, latest run only (docs/DATA_PLATFORM.md §6,
// chart 2): sorted horizontal bars, highest survival first. survival_pct is
// v_survival_by_operator's own number, plotted verbatim as bar width.

export function OperatorsChart({ operators }: { operators: OperatorRow[] }) {
  const sorted = [...operators].sort((a, b) => b.survival_pct - a.survival_pct);

  return (
    <Card title="Survival by operator" aside={<span className={styles.count}>{sorted.length} operators</span>}>
      {sorted.length === 0 ? (
        <p className={styles.muted}>No mutation data for the latest run.</p>
      ) : (
        <ul className={styles.list}>
          {sorted.map((op) => (
            <li key={op.operator} className={styles.item}>
              <div className={styles.row}>
                <span className={styles.file}>{op.operator}</span>
                <span className={styles.count}>{op.survival_pct.toFixed(1)}%</span>
              </div>
              <div className={styles.score}>
                <div className={styles.track} aria-hidden>
                  <div className={styles.fill} style={{ width: `${Math.min(op.survival_pct, 100)}%` }} />
                </div>
              </div>
              <span className={styles.lines}>
                {op.survived} / {op.total} mutants survived
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
