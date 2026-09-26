import type { AnalyzeResponse } from "../lib/types";

export function GapsList({ gaps }: { gaps: AnalyzeResponse["gaps"] }) {
  if (gaps.uncovered_files.length === 0) {
    return <p>No coverage gaps.</p>;
  }
  return (
    <ul>
      {gaps.uncovered_files.map((file) => (
        <li key={file}>
          {file}
          {gaps.missing_lines_by_file[file] && (
            <span> — lines {gaps.missing_lines_by_file[file].join(", ")}</span>
          )}
        </li>
      ))}
    </ul>
  );
}
