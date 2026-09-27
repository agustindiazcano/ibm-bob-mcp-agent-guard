import type { AnalyzeResponse } from "../lib/types";
import { Tooltip } from "./Tooltip";
import styles from "./StatCards.module.css";

type Props = {
  result: AnalyzeResponse;
  gateThreshold: number;
};

export function StatCards({ result, gateThreshold }: Props) {
  const { coverage, mutation, gaps, passed_gate } = result;
  return (
    <div className={styles.grid}>
      <div className={styles.stat}>
        <span className={styles.label}>
          Line coverage
          <Tooltip
            content="Percentage of Python source code lines executed during the test suite. High coverage does not guarantee test assertions are rigorous."
            ariaLabel="About line coverage"
          />
        </span>
        <strong className={styles.value}>{coverage.percent.toFixed(1)}%</strong>
        <span className={styles.detail}>
          {coverage.covered_lines} / {coverage.total_lines} lines
        </span>
      </div>
      <div className={styles.stat}>
        <span className={styles.label}>
          Mutation score
          <Tooltip
            content="Measures if tests catch real bugs: repoguard modifies AST operators (e.g. > to >=, + to -) and runs tests. If tests fail, the mutant is 'killed'. If tests pass, the mutant survived."
            ariaLabel="About mutation score"
          />
        </span>
        {mutation ? (
          <>
            <strong className={styles.value}>{mutation.score.toFixed(2)}%</strong>
            <span className={styles.detail}>
              {mutation.killed} / {mutation.total} mutants killed
            </span>
          </>
        ) : (
          <>
            <strong className={`${styles.value} ${styles.muted}`}>Not run</strong>
            <span className={styles.detail}>Enable &ldquo;Run mutation testing&rdquo;</span>
          </>
        )}
      </div>
      <div className={styles.stat}>
        <span className={styles.label}>
          Files with coverage gaps
          <Tooltip
            content="Number of Python files that contain missing statement or branch execution. Autofix targets these files."
            ariaLabel="About coverage gaps"
          />
        </span>
        <strong className={styles.value}>{gaps.uncovered_files.length}</strong>
        <span className={styles.detail}>{result.risk.length} files ranked by risk</span>
      </div>
      <div className={`${styles.stat} ${passed_gate ? styles.pass : styles.fail}`}>
        <span className={styles.label}>
          Quality gate
          <Tooltip
            content="CI/CD gate status: evaluates whether the repo's measured coverage meets or exceeds the threshold."
            ariaLabel="About quality gate"
          />
        </span>
        <strong className={styles.value}>{passed_gate ? "PASS" : "FAIL"}</strong>
        <span className={styles.detail}>Threshold {gateThreshold}% coverage</span>
      </div>
    </div>
  );
}

