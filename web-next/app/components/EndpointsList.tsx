import type { Endpoint } from "../lib/types";
import { Card } from "./Card";
import styles from "./Lists.module.css";

export function EndpointsList({ endpoints }: { endpoints: Endpoint[] }) {
  // A count of the engine's has_test flags, not a new metric.
  const tested = endpoints.filter((ep) => ep.has_test).length;
  const aside =
    endpoints.length > 0 ? (
      <span className={styles.count}>
        {tested} / {endpoints.length} tested
      </span>
    ) : undefined;

  return (
    <Card title="API endpoints" aside={aside}>
      {endpoints.length === 0 ? (
        <p className={styles.muted}>No FastAPI routes found.</p>
      ) : (
        <ul className={styles.list}>
          {endpoints.map((ep) => (
            <li key={`${ep.file}:${ep.function}:${ep.method}`} className={styles.item}>
              <div className={styles.row}>
                <span className={styles.file}>
                  <span className={styles.method}>{ep.method}</span> {ep.path}
                </span>
                <span className={ep.has_test ? styles.badgePass : styles.badge}>
                  {ep.has_test ? "tested" : "no test"}
                </span>
              </div>
              <span className={styles.lines}>
                {ep.file} · {ep.function}()
              </span>
            </li>
          ))}
        </ul>
      )}
      {endpoints.length > 0 && (
        <p className={styles.note}>
          &ldquo;Tested&rdquo; means a test file mentions the route&rsquo;s path or function name (a static
          check, not a request).
        </p>
      )}
    </Card>
  );
}
