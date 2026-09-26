import type { AnalyzeResponse } from "../lib/types";

export function StatCards({ result }: { result: AnalyzeResponse }) {
  return (
    <div>
      <div>
        <strong>{result.coverage.percent.toFixed(1)}%</strong>
        <span>Line coverage</span>
      </div>
      {result.mutation && (
        <div>
          <strong>{result.mutation.score.toFixed(2)}%</strong>
          <span>
            Mutation score ({result.mutation.killed}/{result.mutation.total})
          </span>
        </div>
      )}
      <div>
        <strong>{result.risk.length}</strong>
        <span>Files ranked by risk</span>
      </div>
      <div>
        <strong>{result.passed_gate ? "PASS" : "FAIL"}</strong>
        <span>Gate</span>
      </div>
    </div>
  );
}
