import type { Metadata } from "next";
import { SlideHeader, SlideShell, Tag, type TagTone } from "../components/site/Page";
import blocks from "../components/site/Blocks.module.css";

export const metadata: Metadata = {
  title: "Features 2",
  description: "Everything else that's real and working today, not roadmap — status and evidence for each.",
};

const ROWS: { feature: string; status: string; tone: TagTone; evidence: string }[] = [
  { feature: "Mutation testing (own AST engine)", status: "Real", tone: "live", evidence: "Measured & documented" },
  { feature: "Self-healing / Autofix", status: "Real", tone: "live", evidence: "Live from the dashboard and CLI" },
  { feature: "Quality gate (repoguard gate)", status: "Real", tone: "live", evidence: "Exists and runs in CI" },
  { feature: "repoguard fix --publish (opens a PR)", status: "Real", tone: "live", evidence: "Implemented in code" },
  { feature: "MCP server (9 tools)", status: "Real", tone: "live", evidence: "Implemented" },
  { feature: "Multicloud (watsonx.ai + Vertex AI)", status: "Real", tone: "live", evidence: "Both working + model selector" },
  { feature: "Guardrails G1-G6 + O1", status: "Real", tone: "live", evidence: "Verified in CI" },
  { feature: "Write guard + AST policy", status: "Real", tone: "live", evidence: "Tested" },
  { feature: "Triple execution + canary", status: "Real", tone: "live", evidence: "Tested" },
  { feature: "Cloud Run + Vercel + Cloud SQL + Terraform + WIF", status: "Real", tone: "live", evidence: "Confirmed" },
  { feature: "Charts (Operators / Survivors / Flaky)", status: "Real", tone: "live", evidence: "Already in the frontend" },
  { feature: "Provider switch + Gemini models", status: "Real", tone: "live", evidence: "Shipped" },
  { feature: "Swarm (S0-S4)", status: "Partial", tone: "gated", evidence: "Parallel lanes done; Critic (S5) + publish (S6) pending" },
  { feature: "IBM Bob usage", status: "Real", tone: "live", evidence: "12 commits, 1st of 6 on the team, evidence in repo" },
];

export default function Features2Page() {
  return (
    <SlideShell>
      <SlideHeader
        eyebrow="Features, continued"
        title="Fourteen more things that are real, not roadmap."
        lead="Every row is either measured in this repo, live in CI, or running in production — with one honestly marked partial."
      />
      <div className={blocks.tableWrap}>
        <table className={blocks.table}>
          <thead>
            <tr>
              <th scope="col">Feature</th>
              <th scope="col">Status</th>
              <th scope="col">Evidence / note</th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map((r) => (
              <tr key={r.feature}>
                <td>{r.feature}</td>
                <td>
                  <Tag tone={r.tone}>{r.status}</Tag>
                </td>
                <td>{r.evidence}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </SlideShell>
  );
}
