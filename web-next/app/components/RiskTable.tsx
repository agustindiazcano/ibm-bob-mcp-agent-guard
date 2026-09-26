import type { AnalyzeResponse } from "../lib/types";

export function RiskTable({ risk }: { risk: AnalyzeResponse["risk"] }) {
  const sorted = [...risk].sort((a, b) => b.score - a.score);
  return (
    <table>
      <thead>
        <tr>
          <th>File</th>
          <th>Score</th>
          <th>Reasons</th>
        </tr>
      </thead>
      <tbody>
        {sorted.map((row) => (
          <tr key={row.file}>
            <td>{row.file}</td>
            <td>{row.score.toFixed(2)}</td>
            <td>{row.reasons.join(", ")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
