import type { AnalyzeResponse } from "../lib/types";
import { Card } from "./Card";
import styles from "./Lists.module.css";

export function RiskTable({ risk }: { risk: AnalyzeResponse["risk"] }) {
  const sorted = [...risk].sort((a, b) => b.score - a.score);
  return (
    <Card title="Risk ranking">
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>File</th>
              <th>Score</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((row) => (
              <tr key={row.file}>
                <td>
                  <div className={styles.file}>{row.file}</div>
                  <div className={styles.reasons}>{row.reasons.join(", ")}</div>
                </td>
                <td className={styles.scoreCell}>
                  <div className={styles.score}>
                    {/* score is the engine's 0–1 uncovered-line ratio (core.compute_risk), so it maps straight to a width */}
                    <div className={styles.track} aria-hidden>
                      <div className={styles.fill} style={{ width: `${row.score * 100}%` }} />
                    </div>
                    <span className={styles.scoreValue}>{row.score.toFixed(2)}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
