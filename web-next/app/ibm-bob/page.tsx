import type { Metadata } from "next";
import { SlideHeader, SlideShell } from "../components/site/Page";
import blocks from "../components/site/Blocks.module.css";

export const metadata: Metadata = {
  title: "Built with IBM Bob",
  description: "Phases 0-8, and Bob's real commit/PR numbers from Bobalytics.",
};

const KPIS = [
  { label: "Bob commits", value: "12", detail: "1st of 6 on the team" },
  { label: "Bob lines", value: "820", detail: "of 5,134 total in this repo" },
  { label: "Bob factor", value: "16.0%", detail: "share of repo lines" },
];

const PHASES = [
  "0 Project skeleton",
  "1 demo-repo fixture",
  "2 Core measurement",
  "3 Mutation engine (own AST)",
  "4 Risk score & dashboard",
  "5 API check",
  "6 Visual testing",
  "7 MCP server",
  "8 Bob modes, rules, skills",
];

export default function IbmBobPage() {
  return (
    <SlideShell>
      <SlideHeader
        eyebrow="Built with IBM Bob"
        title="Phases 0-8 — the engine's entire foundation — authored by IBM Bob."
        lead={
          <>
            Full PR-by-PR, commit-by-commit evidence, including the exact &ldquo;Made with IBM Bob&rdquo; footers, in{" "}
            <code>docs/IBM_BOB_USAGE.md</code>.
          </>
        }
      />
      <div className={blocks.grid3}>
        {KPIS.map((k) => (
          <div key={k.label} className={blocks.tile}>
            <span className={blocks.muted}>{k.label}</span>
            <h3 className={blocks.tileTitle} style={{ fontSize: "28px" }}>
              {k.value}
            </h3>
            <p className={blocks.tileText}>{k.detail}</p>
          </div>
        ))}
      </div>
      <div className={blocks.chips}>
        {PHASES.map((p) => (
          <span key={p} className={blocks.chip}>
            <strong>{p}</strong>
          </span>
        ))}
      </div>
    </SlideShell>
  );
}
