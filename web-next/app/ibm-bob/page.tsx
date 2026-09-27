import type { Metadata } from "next";
import { SlideHeader, SlideShell } from "../components/site/Page";
import blocks from "../components/site/Blocks.module.css";

export const metadata: Metadata = {
  title: "Built with IBM Bob",
  description: "Phases 0-8, Bob's real commit/PR numbers from Bobalytics, and the AI-assisted flow that took over from there.",
};

const KPIS = [
  { label: "Bob commits", value: "12", detail: "1st of 6 on the team" },
  { label: "Bob PRs", value: "4", detail: "#1, #2, #4, #6" },
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

const SCREENSHOTS = [
  {
    file: "10-bob-ide-2026-09-25_16-42-home-welcome-screen-recent-tasks.png",
    alt: "IBM Bob IDE welcome screen showing this project's recent tasks",
    caption: "Bob IDE, this project's workspace",
  },
  {
    file: "3-bob-ide-2026-09-25_15-05-github-pr-title-description-draft-markdown.png",
    alt: "IBM Bob drafting a GitHub PR title and description",
    caption: "Bob drafting a PR description",
  },
  {
    file: "9-bob-ide-2026-09-25_15-45-phase0-complete-summary-verification-pass.png",
    alt: "IBM Bob completing Phase 0 with a verify.py PASS",
    caption: "Phase 0 closed, verify.py PASS",
  },
  {
    file: "11-bob-ide-2026-09-25_16-35-phase8-test-writer-subagent-mode-setup.png",
    alt: "IBM Bob setting up the Phase 8 Test Writer subagent mode",
    caption: "Phase 8: Test Writer subagent mode",
  },
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
      <div className={blocks.grid4}>
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
      <div className={blocks.callout}>
        <span className={blocks.calloutTitle}>After Phase 8: the AI-assisted flow took over</span>
        <p className={blocks.tileText}>
          Bob&rsquo;s handoff (PR #7, &ldquo;Bob is execution-only now&rdquo;) is itself a Bob-era artifact. From
          there, context between sessions was carried in plain files instead of re-explaining the project each
          time: <code>AGENTS.md</code> for the standing rules, <code>LASTCONTEXT.md</code> to save what happened at
          the end of every session, and <code>PENDING.md</code> as the running task tracker. Reading three short
          files instead of re-deriving project state from scratch is what kept every session&rsquo;s planning cheap
          in tokens.
        </p>
      </div>
      <div className={blocks.grid4}>
        {SCREENSHOTS.map((s) => (
          <div key={s.file} className={blocks.tile} style={{ padding: 0, overflow: "hidden" }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={`/bob-evidence/${s.file}`} alt={s.alt} style={{ width: "100%", display: "block" }} />
            <p className={blocks.tileText} style={{ padding: "8px 10px 10px" }}>
              {s.caption}
            </p>
          </div>
        ))}
      </div>
    </SlideShell>
  );
}
