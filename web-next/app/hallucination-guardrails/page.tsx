import type { Metadata } from "next";
import { SlideHeader, SlideShell } from "../components/site/Page";
import blocks from "../components/site/Blocks.module.css";

export const metadata: Metadata = {
  title: "Anti-Hallucination Guardrails",
  description: "G1-G6 and O1: what stops the AI from gaming or hallucinating its own mutation score, verified in CI.",
};

const GUARDRAILS: { id: string; stops: string; ci: string }[] = [
  { id: "G1 · Env allow-list", stops: "Leaked or hallucinated server secrets (tokens, API keys) inside a generated test", ci: "phase19-env" },
  { id: "G2 · Policy AST", stops: "Tests with no real assertions, source-file reads, hashing, or pytest-hook tricks", ci: "phase19-policy" },
  { id: "G3 · Acceptance gate", stops: "Flaky tests, order-dependent tricks, canaries, vandalizing existing tests", ci: "phase19-accept" },
  { id: "G4 · Mutation integrity", stops: "Harness errors miscounted as “killed” mutants", ci: "engine-parallel-mutation" },
  { id: "G5 · Status & evidence", stops: "A false-positive report, or publishing without a real score increase", ci: "fix-loop-stub" },
  { id: "G6 · Source-only coverage", stops: "Coverage inflated by counting the tests' own lines", ci: "quality-gate" },
  { id: "O1 · Structured run record", stops: "Lost traceability of what the model actually did", ci: "fix-loop-stub" },
];

export default function HallucinationGuardrailsPage() {
  return (
    <SlideShell>
      <SlideHeader
        eyebrow="Anti-hallucination"
        title="LLMs can cheat. We don't let them."
        lead="An unguarded model can hallucinate trivial assertions, or read source and hash it to inflate mutation score to a fake 100%. All seven guardrails below are built and green in CI today — not a plan."
      />
      <div className={blocks.tableWrap}>
        <table className={blocks.table}>
          <thead>
            <tr>
              <th>Guardrail</th>
              <th>Neutralizes</th>
              <th>CI job</th>
            </tr>
          </thead>
          <tbody>
            {GUARDRAILS.map((g) => (
              <tr key={g.id}>
                <td>{g.id}</td>
                <td>{g.stops}</td>
                <td>
                  <code>{g.ci}</code> ✅
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </SlideShell>
  );
}
