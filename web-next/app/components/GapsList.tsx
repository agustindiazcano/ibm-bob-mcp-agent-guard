import type { AnalyzeResponse } from "../lib/types";
import { Card } from "./Card";
import styles from "./Lists.module.css";

export function GapsList({ gaps }: { gaps: AnalyzeResponse["gaps"] }) {
  return (
    <Card title="Coverage gaps">
      {gaps.uncovered_files.length === 0 ? (
        <p className={styles.none}>No coverage gaps.</p>
      ) : (
        <ul className={styles.list}>
          {gaps.uncovered_files.map((file) => {
            const lines = gaps.missing_lines_by_file[file] ?? [];
            return (
              <li key={file} className={styles.item}>
                <div className={styles.row}>
                  <span className={styles.file}>{file}</span>
                  <span className={styles.badge}>
                    {lines.length} {lines.length === 1 ? "line" : "lines"}
                  </span>
                </div>
                {lines.length > 0 && <span className={styles.lines}>{lines.join(", ")}</span>}
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}
