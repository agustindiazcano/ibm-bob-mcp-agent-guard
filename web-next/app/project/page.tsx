import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import { ButtonLink, PageHeader, PageShell, Section, Tag, type TagTone } from "../components/site/Page";
import { Icon, type IconName } from "../components/site/Icon";
import { repoDoc } from "../components/site/links";
import blocks from "../components/site/Blocks.module.css";
import { DEMO_REPO_RESULTS } from "../lib/measured";
import styles from "./project.module.css";

export const metadata: Metadata = {
  title: "Project",
  description: "What TestMind AI is, what it measures, and how you use it.",
};

const FEATURES: { icon: IconName; title: string; text: ReactNode }[] = [
  {
    icon: "bug",
    title: "Mutation testing",
    text: (
      <>
        Injects one small bug at a time (flipped comparisons, swapped operators, changed constants,{" "}
        <code>return None</code>, removed <code>raise</code>) with its own AST engine and reruns the suite. A mutant that
        survives is a bug the tests would miss.
      </>
    ),
  },
  {
    icon: "tests",
    title: "Writes the missing tests",
    text: (
      <>
        A test-writer agent and a critic agent take the riskiest files, one at a time, and write tests through a tool
        that can only write under <code>tests/</code>. The engine then re-measures.
      </>
    ),
  },
  {
    icon: "api",
    title: "API checks",
    text: "Finds a FastAPI app's routes by parsing its source, flags endpoints no test calls, and smoke-tests GET endpoints for 5xx errors.",
  },
  {
    icon: "eye",
    title: "Visual regression",
    text: "Screenshots a running page with Playwright and diffs it pixel by pixel against a baseline, plus console errors and basic accessibility checks.",
  },
  {
    icon: "risk",
    title: "Risk ranking",
    text: "Ranks files by the share of their lines no test runs, so the fix loop and the reader both start where the suite is weakest.",
  },
  {
    icon: "shield",
    title: "Quality gate",
    text: "Pass/fail against a coverage threshold you choose, from the web UI, the CLI (repoguard gate) or CI.",
  },
];

const FLOW: { title: string; text: string; href?: string; cta?: string; tag: string; tone: TagTone }[] = [
  {
    title: "Analyze",
    text: "Point it at a repo on the backend's machine. It runs the suite, coverage and, optionally, mutation testing.",
    href: "/",
    cta: "Open Analyze",
    tag: "Live",
    tone: "live",
  },
  {
    title: "Read the gaps",
    text: "Coverage next to mutation score, uncovered lines per file, the risk ranking and the gate result, on the same screen as the run.",
    tag: "Live",
    tone: "live",
  },
  {
    title: "Autofix",
    text: "From Analyze, with a token: the two agents write tests on a temporary copy of the repo, and you get the engine's before/after and the files they wrote.",
    tag: "Token-gated",
    tone: "gated",
  },
  {
    title: "Track results",
    text: "Stored runs per project: coverage vs. mutation over time, which bug kinds survive, and what each fix run changed.",
    href: "/results",
    cta: "Open Results",
    tag: "Phase 17",
    tone: "planned",
  },
];

const ENTRY_POINTS: { icon: IconName; title: string; text: string; code: string }[] = [
  {
    icon: "terminal",
    title: "Terminal",
    text: "Measure, gate a CI job, or run the fix loop.",
    code: "repoguard analyze ./demo-repo --mutation\nrepoguard gate ./demo-repo --threshold 80\nrepoguard fix ./demo-repo",
  },
  {
    icon: "globe",
    title: "Web",
    text: "This dashboard on Vercel, calling the FastAPI backend on Cloud Run.",
    code: "repoguard serve   # backend on :8000\nnpm run dev       # web-next on :3000",
  },
  {
    icon: "plug",
    title: "Any MCP client",
    text: "Nine tools over stdio, compact responses by default, for Claude Code or any other agent.",
    code: "repoguard mcp",
  },
];

export default function ProjectPage() {
  return (
    <PageShell>
      <PageHeader
        eyebrow="The project"
        title="Coverage tells you which lines ran. TestMind AI checks whether your tests would notice a bug."
        lead="It injects bugs into a Python repo on purpose, measures how many the test suite catches, and then has two AI agents write the tests that are missing. The AI decides what to test; the engine does all the measuring."
        actions={
          <>
            <ButtonLink href="/">Analyze a repository</ButtonLink>
            <ButtonLink href="/results" variant="secondary">
              Results dashboard
            </ButtonLink>
          </>
        }
      />

      <Section
        id="results"
        title="The gap coverage hides"
        intro="The bundled demo-repo is a small shop app whose tests run most of the code but assert very little, on purpose."
      >
        <div className={blocks.grid4}>
          {DEMO_REPO_RESULTS.map((row) => (
            <div key={row.label} className={`${styles.metric} ${row.emphasis ? styles.metricEmphasis : ""}`}>
              <span className={styles.metricLabel}>{row.label}</span>
              <span className={styles.metricValues}>
                <span className={styles.before}>{row.before}</span>
                <span className={styles.arrow} aria-label="to">
                  →
                </span>
                <strong className={styles.after}>{row.after}</strong>
              </span>
              {row.detail && <span className={styles.metricDetail}>{row.detail}</span>}
            </div>
          ))}
        </div>
        <p className={styles.caption}>
          Measured by the engine on <code>demo-repo</code>. Before: its 5 deliberately weak tests, 65.1% coverage but only
          about 1 bug in 5 caught. After: the reference tests in{" "}
          <a href={repoDoc("docs/expected-after-tests")} target="_blank" rel="noreferrer">
            docs/expected-after-tests/
          </a>
          . A live run of the fix loop on Gemini 3 reached the same 89.87% (71/79). The 8 mutants still alive are
          equivalent: changes no test can observe.
        </p>
      </Section>

      <Section id="what" title="What it does">
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
      </Section>

      <Section
        id="flow"
        title="How you use it"
        intro="Four screens, in the order you'd use them. The first three work today on the public demo."
      >
        <ol className={blocks.steps}>
          {FLOW.map((s) => (
            <li key={s.title} className={`${blocks.tile} ${blocks.step}`}>
              <div className={blocks.tileHead}>
                <h3 className={blocks.tileTitle}>{s.title}</h3>
                <Tag tone={s.tone}>{s.tag}</Tag>
              </div>
              <p className={blocks.tileText}>{s.text}</p>
              {s.href && (
                <Link href={s.href} className={blocks.stepLink}>
                  {s.cta} →
                </Link>
              )}
            </li>
          ))}
        </ol>
      </Section>

      <Section id="ways-in" title="Three ways in" intro="One engine behind all of them, so the numbers match wherever you read them.">
        <div className={blocks.grid3}>
          {ENTRY_POINTS.map((e) => (
            <div key={e.title} className={blocks.tile}>
              <div className={styles.entryHead}>
                <span className={blocks.icon}>
                  <Icon name={e.icon} />
                </span>
                <h3 className={blocks.tileTitle}>{e.title}</h3>
              </div>
              <p className={blocks.tileText}>{e.text}</p>
              <pre className={blocks.pre}>{e.code}</pre>
            </div>
          ))}
        </div>
      </Section>

      <Section id="principles" title="What it will and won't do">
        <div className={blocks.grid2}>
          <div className={blocks.callout}>
            <span className={blocks.calloutTitle}>The AI decides, the engine measures.</span>
            <span className={blocks.muted}>
              No number on any screen comes from a model. Coverage, mutation score, risk and endpoint counts are engine
              output; AI text is labeled advisory.
            </span>
          </div>
          <div className={blocks.callout}>
            <span className={blocks.calloutTitle}>Source code is the reference.</span>
            <span className={blocks.muted}>
              The agents can only write under <code>tests/</code>. A new test that fails against the real code is treated
              as a wrong test, not a reason to change the code.
            </span>
          </div>
        </div>
        <ul className={blocks.list}>
          <li>Python and pytest only; API checks support FastAPI only.</li>
          <li>
            Two agents in sequence (writer, then critic), not a parallel swarm yet. The swarm is designed but not built
            (Phase 18).
          </li>
          <li>Equivalent mutants are reported, not filtered out automatically.</li>
          <li>Run history, and the charts built on it, arrive with the database in Phase 17.</li>
        </ul>
      </Section>
    </PageShell>
  );
}
