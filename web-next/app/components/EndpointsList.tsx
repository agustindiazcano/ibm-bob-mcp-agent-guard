import type { Endpoint } from "../lib/types";
import { Card } from "./Card";
import { Tooltip } from "./Tooltip";
import styles from "./Lists.module.css";

export function EndpointsList({ endpoints }: { endpoints: Endpoint[] }) {
  // A count of the engine's has_test flags, not a new metric.
  const tested = endpoints.filter((ep) => ep.has_test).length;
  const aside =
    endpoints.length > 0 ? (
      <span className={styles.count}>
        {tested} / {endpoints.length} tested
        <Tooltip
          content="Detects whether FastAPI route handlers are invoked or referenced in tests via AST analysis. Testing an internal service/class (e.g. Cart) does not verify its HTTP route."
          ariaLabel="About endpoint test detection"
        />
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
                <span
                  className={ep.has_test ? styles.badgePass : styles.badge}
                  title={
                    ep.has_test
                      ? "A test file directly targets or references this HTTP route or handler."
                      : "No test directly exercises this route. Even if internal classes have unit tests, the HTTP endpoint is untested."
                  }
                >
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
          <strong>How endpoints are checked:</strong> AST static analysis looks for test references to the endpoint&rsquo;s route path or handler function. If your unit tests exercise internal logic (e.g. <code>cart.py</code>) directly without calling the FastAPI route (e.g. <code>/cart</code> in <code>api.py</code>), the endpoint is correctly flagged as <code>no test</code>.
        </p>
      )}
    </Card>
  );
}

