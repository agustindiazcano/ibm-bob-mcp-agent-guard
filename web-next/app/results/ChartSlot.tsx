import type { ReactNode } from "react";
import type { Loaded, Row } from "./history";
import styles from "./results.module.css";

// One chart position on /results. It owns the frame and the states
// (loading, unavailable, no runs yet); the chart itself comes in through
// `children` once it's built. Until then, rows show in the table view,
// which stays under the chart afterwards as its accessible twin.

type Props = {
  index: number;
  title: string;
  question: string;
  form: string;
  source: string;
  state: Loaded<Row[]>;
  wide?: boolean;
  children?: ReactNode;
};

const MAX_TABLE_ROWS = 50;

function DataTable({ rows }: { rows: Row[] }) {
  const columns = Object.keys(rows[0]);
  const shown = rows.slice(0, MAX_TABLE_ROWS);
  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c} scope="col">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {shown.map((row, i) => (
            <tr key={i}>
              {columns.map((c) => (
                <td key={c}>{row[c] === null || row[c] === undefined ? "—" : String(row[c])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > shown.length && (
        <p className={styles.tableNote}>
          First {shown.length} of {rows.length} rows.
        </p>
      )}
    </div>
  );
}

function Body({ state, children }: { state: Loaded<Row[]>; children?: ReactNode }) {
  if (state.status === "loading") {
    return <div className={styles.placeholder}>Loading…</div>;
  }
  if (state.status === "unavailable") {
    return <div className={styles.placeholder}>{state.reason.kind === "no-api" ? "Waiting for run history (Phase 17)" : state.reason.message}</div>;
  }
  if (state.data.length === 0) {
    return <div className={styles.placeholder}>No runs yet</div>;
  }
  return (
    <>
      {children ?? (
        <div className={styles.placeholder}>
          Chart not built yet &middot; {state.data.length} {state.data.length === 1 ? "row" : "rows"} received
        </div>
      )}
      <details className={styles.tableView} open={!children}>
        <summary>Table view</summary>
        <DataTable rows={state.data} />
      </details>
    </>
  );
}

export function ChartSlot({ index, title, question, form, source, state, wide, children }: Props) {
  return (
    <figure className={`${styles.slot} ${wide ? styles.wide : ""}`} aria-busy={state.status === "loading"}>
      <figcaption className={styles.slotHead}>
        <span className={styles.slotIndex}>{index}</span>
        <div className={styles.slotTitles}>
          <h2 className={styles.slotTitle}>{title}</h2>
          <p className={styles.slotQuestion}>{question}</p>
        </div>
        <span className={styles.slotMeta}>
          {form}
          <code>{source}</code>
        </span>
      </figcaption>
      <Body state={state}>{children}</Body>
    </figure>
  );
}
