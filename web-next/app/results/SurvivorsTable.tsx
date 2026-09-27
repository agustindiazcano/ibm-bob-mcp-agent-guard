import type { SurvivorRow } from "./history";
import { Card } from "../components/Card";
import styles from "../components/Lists.module.css";

// Mutants that have never been killed across every non-dirty run
// (docs/DATA_PLATFORM.md §6, chart 5: v_persistent_survivors). A formatted
// table, not the generic raw-column fallback ChartSlot already provides.

function formatDate(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function SurvivorsTable({ survivors }: { survivors: SurvivorRow[] }) {
  const sorted = [...survivors].sort((a, b) => b.runs_seen - a.runs_seen);

  return (
    <Card title="Persistent survivors" aside={<span className={styles.count}>{sorted.length} found</span>}>
      {sorted.length === 0 ? (
        <p className={styles.muted}>No mutant has survived every run yet.</p>
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>File / function</th>
                <th>Mutation</th>
                <th>Seen</th>
                <th>First seen</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((s) => (
                <tr key={s.fingerprint}>
                  <td>
                    <div className={styles.file}>{s.file_path}</div>
                    <div className={styles.lines}>{s.function_name}()</div>
                  </td>
                  <td className={styles.reasons}>{s.description}</td>
                  <td className={styles.count}>{s.runs_seen} runs</td>
                  <td className={styles.lines}>{formatDate(s.first_seen)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
