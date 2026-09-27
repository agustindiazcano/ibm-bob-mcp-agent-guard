import type { Metadata } from "next";
import { SlideHeader, SlideShell } from "../components/site/Page";
import { Icon, type IconName } from "../components/site/Icon";
import blocks from "../components/site/Blocks.module.css";

export const metadata: Metadata = {
  title: "Features",
  description: "What TestMind AI actually does today — from the README, not aspirational.",
};

const FEATURES: { icon: IconName; title: string; text: string }[] = [
  {
    icon: "bug",
    title: "Mutation testing",
    text: "Own AST engine, 6 operators. Injects one bug at a time, reruns the suite. A surviving mutant is a bug your tests would miss.",
  },
  {
    icon: "tests",
    title: "Self-healing (writes the missing tests)",
    text: "repoguard fix hands surviving mutants to a writer + critic AI, guarded to write only under tests/, then re-measures for real.",
  },
  {
    icon: "api",
    title: "API checks",
    text: "Finds a FastAPI app's routes by parsing its source, flags endpoints no test calls, smoke-tests GET for 5xx errors.",
  },
  {
    icon: "eye",
    title: "Visual regression",
    text: "Playwright screenshot vs. baseline, pixel diff, console errors, basic accessibility (axe-core). MCP tools today.",
  },
  {
    icon: "risk",
    title: "Risk ranking & dashboard",
    text: "Ranks files by uncovered-line share; builds the HTML/web dashboard the fix loop prioritizes from.",
  },
  {
    icon: "shield",
    title: "Quality gate",
    text: "Pass/fail against a coverage threshold — from the web UI, the CLI (repoguard gate), or CI.",
  },
];

export default function FeaturesPage() {
  return (
    <SlideShell>
      <SlideHeader
        eyebrow="Features"
        title="Six things it measures or does today — not a roadmap."
        lead="The AI decides what to test; deterministic tools do every measurement. No number on any screen comes from a model."
      />
      <div className={blocks.grid3}>
        {FEATURES.map((f) => (
          <div key={f.title} className={blocks.tile}>
            <span className={blocks.icon}>
              <Icon name={f.icon} />
            </span>
            <h3 className={blocks.tileTitle}>{f.title}</h3>
            <p className={blocks.tileText}>{f.text}</p>
          </div>
        ))}
      </div>
    </SlideShell>
  );
}
