"use client";

type Props = {
  onAnalyze: () => void;
  onGate: () => void;
  busy: boolean;
};

export function ActionBar({ onAnalyze, onGate, busy }: Props) {
  return (
    <div>
      <button type="button" onClick={onAnalyze} disabled={busy}>
        Analyze
      </button>
      <button type="button" onClick={onGate} disabled={busy}>
        Gate
      </button>
      <button type="button" disabled title="Coming soon — needs POST /api/fix (PENDING-front.md gap 3)">
        Autofix
      </button>
    </div>
  );
}
