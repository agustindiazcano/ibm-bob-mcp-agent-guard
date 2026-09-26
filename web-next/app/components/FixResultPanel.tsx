import type { Dashboard, FixDone } from "../lib/types";
import { Card } from "./Card";
import styles from "./FixResultPanel.module.css";

function Metric({ label, before, after }: { label: string; before: string; after: string }) {
  return (
    <div className={styles.metric}>
      <span className={styles.label}>{label}</span>
      <span className={styles.values}>
        <span className={styles.before}>{before}</span>
        <span aria-hidden> → </span>
        <strong>{after}</strong>
      </span>
    </div>
  );
}

function mutationText(d: Dashboard | null): string {
  if (!d?.mutation) {
    return "not measured";
  }
  return `${d.mutation.score.toFixed(2)}% (${d.mutation.killed}/${d.mutation.total})`;
}

function coverageText(d: Dashboard | null): string {
  return d ? `${d.coverage.percent.toFixed(1)}%` : "not measured";
}

// Numbers are the engine's before/after dashboards, shown as-is. The tests
// were written into a temporary copy on the server; nothing was committed.
export function FixResultPanel({ fix }: { fix: FixDone }) {
  return (
    <>
      <Card title="Autofix result" aside={<span className={styles.provider}>via {fix.provider}</span>}>
        <div className={styles.metrics}>
          <Metric label="Mutation score" before={mutationText(fix.before)} after={mutationText(fix.after)} />
          <Metric label="Line coverage" before={coverageText(fix.before)} after={coverageText(fix.after)} />
        </div>
        <p className={styles.note}>
          Tests were written to a temporary copy of the repo on the server and discarded after measuring. Copy the
          ones you want into your repo&rsquo;s <code>tests/</code>.
        </p>
        {fix.files.length === 0 ? (
          <p className={styles.note}>No test files were written.</p>
        ) : (
          <ul className={styles.files}>
            {fix.files.map((file) => (
              <li key={file.path}>
                <details>
                  <summary>
                    <code>{file.path}</code> <span className={styles.status}>{file.status}</span>
                  </summary>
                  <pre className={styles.code}>{file.content}</pre>
                </details>
              </li>
            ))}
          </ul>
        )}
      </Card>
      {fix.critic_notes.length > 0 && (
        <Card title="Critic notes" aside={<span className={styles.tag}>Advisory, not a measurement</span>}>
          <ul className={styles.notes}>
            {fix.critic_notes.map((note, i) => (
              <li key={i}>{note}</li>
            ))}
          </ul>
        </Card>
      )}
    </>
  );
}
