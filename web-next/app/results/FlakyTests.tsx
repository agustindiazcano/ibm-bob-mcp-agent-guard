import type { FlakyRow } from "./history";
import { Card } from "../components/Card";
import styles from "../components/Lists.module.css";

// Tests whose outcome varied across repeated runs of the same commit
// (docs/DATA_PLATFORM.md §6, chart 6: v_flaky_tests). A formatted table,
// not the generic raw-column fallback ChartSlot already provides.

export function FlakyTests({ tests }: { tests: FlakyRow[] }) {
  const sorted = [...tests].sort((a, b) => b.distinct_outcomes - a.distinct_outcomes || b.runs - a.runs);

  return (
    <Card title="Flaky tests" aside={<span className={styles.count}>{sorted.length} found</span>}>
      {sorted.length === 0 ? (
        <p className={styles.muted}>No test changed outcome across repeated runs of the same commit.</p>
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Test</th>
                <th>Commit</th>
                <th>Outcomes seen</th>
                <th>Runs</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((t) => (
                <tr key={`${t.commit_sha}:${t.test_id}`}>
                  <td className={styles.file}>{t.test_id}</td>
                  <td className={styles.lines}>{t.commit_sha.slice(0, 7)}</td>
                  <td>
                    <span className={styles.badge}>{t.distinct_outcomes}</span>
                  </td>
                  <td className={styles.count}>{t.runs}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
