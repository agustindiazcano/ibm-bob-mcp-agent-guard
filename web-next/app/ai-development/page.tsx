import type { Metadata } from "next";
import { BobBadge } from "../components/site/Brand";
import { PageHeader, PageShell, Section, Tag } from "../components/site/Page";
import { repoDoc } from "../components/site/links";
import blocks from "../components/site/Blocks.module.css";
import styles from "./aiDevelopment.module.css";

export const metadata: Metadata = {
  title: "AI-assisted development",
  description: "How TestMind AI itself is built: AI agents under a file-based contract, checked against measured output.",
};

const LOOP = [
  "New task",
  "Fresh session",
  "Read CLAUDE.md · PENDING.md · LASTCONTEXT.md",
  "Branch",
  "Plan → code → tests",
  "scripts/verify.py",
  "PR with the verify output",
  "Human reviews and merges",
  "Update PENDING.md + LASTCONTEXT.md",
];

const CONTRACT: { file: string; role: string }[] = [
  {
    file: "CLAUDE.md / AGENTS.md",
    role: "Architecture rules, layer boundaries, the verification table and the actions that need human sign-off. Kept byte-identical so every agent reads the same rules.",
  },
  { file: "PENDING.md", role: "The prioritized backlog, phase by phase. Items are checked off as they land, never deleted." },
  {
    file: "LASTCONTEXT.md",
    role: "Where things stand: what's done, what's mid-flight, decisions already made and gotchas still in effect. A new session reads this instead of re-deriving it from history.",
  },
  { file: "scripts/verify.py", role: "The phase gates. A change isn't done without a PASS, pasted into the PR as the test plan." },
];

const CAUGHT: { looked: string; actual: string; guard: string }[] = [
  {
    looked: "Mutation score 100% (79/79), identical on two runs",
    actual: "pytest resolved through PATH to an environment without it, so every mutant run failed and counted as killed.",
    guard: "Subprocesses use sys.executable; the check also asserts the known baseline, 16/79.",
  },
  {
    looked: "Mutation score 100% (79/79) after an AI fix run",
    actual: "The AI-written tests failed on the unmodified code, so every mutant inherited those failures.",
    guard: "The unmodified suite must pass before any mutant runs, or the engine refuses.",
  },
  {
    looked: "Accessibility: 0 violations",
    actual: "axe-playwright-python was never installed, so the check never ran.",
    guard: "Declared as a dependency; a check that can't run returns ok=false with the error.",
  },
  {
    looked: "Fix loop crashed mid-run",
    actual: "The model asked to read a file that doesn't exist, and the raw error escaped the loop.",
    guard: "Tool errors go back to the model as a normal result it can correct.",
  },
];

export default function AiDevelopmentPage() {
  return (
    <PageShell>
      <PageHeader
        eyebrow="AI-assisted development"
        title="Built by AI agents, checked against measurements."
        lead="This repo is written by AI coding agents working under an explicit contract kept in the repo itself. The human sets direction, approves risky changes and checks every claim against scripts/verify.py's output, never against an agent's own summary."
      />

      <Section id="generations" title="Two generations">
        <div className={styles.timeline}>
          <div className={styles.era}>
            <div className={styles.eraHead}>
              <span className={styles.eraVersion}>1.0</span>
              <h3 className={blocks.tileTitle}>Built on IBM Bob</h3>
              <Tag tone="planned">Retired</Tag>
            </div>
            <p className={blocks.tileText}>
              IBM Bob authored the foundation and Phases 0&ndash;8: the engine, the demo-repo fixture, the mutation engine,
              compact MCP responses, and a <code>.bob/</code> swarm of custom modes (Orchestrator, Test Writer, Critic,
              Gate, Publisher) with hooks that kept writes inside <code>tests/</code>.
            </p>
            <p className={styles.eraFact}>12 Bob commits, ranked 1st by Bob commits in the hackathon.</p>
          </div>
          <div className={`${styles.era} ${styles.eraCurrent}`}>
            <div className={styles.eraHead}>
              <span className={styles.eraVersion}>2.0</span>
              <h3 className={blocks.tileTitle}>Bob&rsquo;s roles, as code</h3>
              <BobBadge size="sm" />
            </div>
            <p className={blocks.tileText}>
              The writer and critic roles now run in <code>watson_agent/</code> on watsonx.ai or Vertex AI, callable from
              the terminal or the Autofix button. The hooks became properties of the code: a write guard that rejects
              anything outside <code>tests/</code>, and a run report written after every fix. Claude Code authors the repo
              from Phase 13 on, under the same contract.
            </p>
            <p className={styles.eraFact}>First live fix-loop success: 20.25% → 89.87% mutation score on demo-repo.</p>
          </div>
        </div>
      </Section>

      <Section
        id="loop"
        title="The session loop"
        intro="Every task starts from a clean context and three short files. Re-reading them is cheaper than carrying a long session's dead ends forward."
      >
        <ol className={styles.loop}>
          {LOOP.map((step, i) => (
            <li key={step} className={styles.loopStep}>
              <span className={styles.loopIndex}>{i + 1}</span>
              <span>{step}</span>
            </li>
          ))}
          <li className={styles.loopBack} aria-label="Then back to step 1">
            ↺ next task
          </li>
        </ol>
      </Section>

      <Section id="contract" title="The contract lives in the repo">
        <div className={blocks.tableWrap}>
          <table className={blocks.table}>
            <thead>
              <tr>
                <th scope="col">File</th>
                <th scope="col">Role</th>
              </tr>
            </thead>
            <tbody>
              {CONTRACT.map((c) => (
                <tr key={c.file}>
                  <td>
                    <code>{c.file}</code>
                  </td>
                  <td>{c.role}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section
        id="caught"
        title="Verification over trust"
        intro="Real results that looked fine and weren't, each found by checking a number against an independent one. Each now has a guard in the code."
      >
        <div className={blocks.grid2}>
          {CAUGHT.map((c) => (
            <div key={c.looked} className={`${blocks.tile} ${styles.case}`}>
              <span className={styles.caseLabel}>Looked like</span>
              <p className={styles.caseLooked}>{c.looked}</p>
              <span className={styles.caseLabel}>Actually</span>
              <p className={blocks.tileText}>{c.actual}</p>
              <span className={styles.caseLabel}>Guard now</span>
              <p className={blocks.tileText}>{c.guard}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section id="roles" title="Who does what">
        <div className={blocks.grid2}>
          <div className={blocks.tile}>
            <h3 className={blocks.tileTitle}>The agent</h3>
            <ul className={blocks.list}>
              <li>Plans the change from PENDING.md and the rules that apply</li>
              <li>Writes code and tests inside the layer boundaries</li>
              <li>Runs the matching verify.py check; no PASS, not done</li>
              <li>Reviews its own diff against the ask-first list</li>
              <li>Branch, Conventional Commit, PR with the verify output</li>
            </ul>
          </div>
          <div className={blocks.tile}>
            <h3 className={blocks.tileTitle}>The human</h3>
            <ul className={blocks.list}>
              <li>Sets direction and priorities</li>
              <li>Approves anything on the ask-first list: demo-repo source, the write guard, mutation operators, published numbers</li>
              <li>Runs the steps that need real cloud access: IAM grants, secrets</li>
              <li>Reviews and merges every PR</li>
            </ul>
          </div>
        </div>
        <p className={blocks.muted}>
          Full write-up:{" "}
          <a href={repoDoc("docs/AI_ASSISTED_DEVELOPMENT_FRAMEWORK.md")} target="_blank" rel="noreferrer">
            AI_ASSISTED_DEVELOPMENT_FRAMEWORK.md
          </a>{" "}
          ·{" "}
          <a href={repoDoc("docs/IBM_BOB_USAGE.md")} target="_blank" rel="noreferrer">
            IBM_BOB_USAGE.md
          </a>
        </p>
      </Section>
    </PageShell>
  );
}
