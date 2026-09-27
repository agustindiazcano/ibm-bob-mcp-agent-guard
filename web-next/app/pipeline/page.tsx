import type { Metadata } from "next";
import { ButtonLink, PageHeader, PageShell, Section } from "../components/site/Page";
import { Icon, type IconName } from "../components/site/Icon";
import { REPO_URL } from "../components/site/links";
import blocks from "../components/site/Blocks.module.css";

export const metadata: Metadata = {
  title: "Ship it",
  description: "TestMind AI installs as a real Python package with one command and plugs straight into any CI/CD pipeline.",
};

const INSTALL: { icon: IconName; title: string; text: string; code: string }[] = [
  {
    icon: "terminal",
    title: "Install",
    text: "One command, directly from GitHub — no PyPI publish required for this to work today.",
    code: "pip install git+https://github.com/agustindiazcano/ibm-bob-mcp-agent-guard.git",
  },
  {
    icon: "shield",
    title: "With AI (self-healing)",
    text: "Adds the Vertex AI extra so the fix loop can write missing tests.",
    code: 'pip install "repoguard[vertex] @ git+https://github.com/agustindiazcano/ibm-bob-mcp-agent-guard.git"',
  },
  {
    icon: "check",
    title: "Use it",
    text: "Same three commands whether it's your laptop or a CI runner.",
    code: "repoguard analyze ./your-repo --mutation\nrepoguard gate ./your-repo --threshold 80\nrepoguard fix ./your-repo --publish",
  },
];

const CI_YAML = `- name: Install TestMind AI
  run: pip install "repoguard[vertex] @ git+https://github.com/agustindiazcano/ibm-bob-mcp-agent-guard.git"

- name: Quality gate — fail the build if tests don't really catch bugs
  run: repoguard gate . --threshold 80

- name: Self-healing autofix (writes missing tests, opens a PR)
  if: failure()
  run: repoguard fix . --publish
  env:
    VERTEX_PROJECT_ID: \${{ secrets.VERTEX_PROJECT_ID }}`;

export default function PipelinePage() {
  return (
    <PageShell>
      <PageHeader
        eyebrow="Ship it"
        title="Not a demo app. A package that installs with one command and lives inside your pipeline."
        lead="repoguard is a real, installable Python package — pip install, one line, verified in a clean throwaway environment. That means it drops straight into any existing CI/CD pipeline: every pull request can run a real quality gate, and a failing gate can trigger self-healing before a human ever looks at it."
        actions={
          <ButtonLink href={REPO_URL} variant="secondary">
            View on GitHub
          </ButtonLink>
        }
      />

      <Section
        id="install"
        title="Install it in one command"
        intro="Verified live in an isolated venv this session: pip install, repoguard --help, and a real measurement against demo-repo — same numbers as everywhere else."
      >
        <div className={blocks.grid3}>
          {INSTALL.map((s) => (
            <div key={s.title} className={blocks.tile}>
              <div className={blocks.tileHead}>
                <span className={blocks.icon}>
                  <Icon name={s.icon} />
                </span>
                <h3 className={blocks.tileTitle}>{s.title}</h3>
              </div>
              <p className={blocks.tileText}>{s.text}</p>
              <pre className={blocks.pre}>{s.code}</pre>
            </div>
          ))}
        </div>
      </Section>

      <Section
        id="pipeline"
        title="Wire it into CI/CD"
        intro="The same commands you just ran locally, as pipeline steps. A weak suite fails the build; the fix loop can answer with a self-healing PR before a human is paged."
      >
        <pre className={blocks.pre}>{CI_YAML}</pre>
      </Section>

      <Section id="why" title="Why this matters beyond the demo">
        <div className={blocks.grid2}>
          <div className={blocks.callout}>
            <span className={blocks.calloutTitle}>Reduces fragility before it ships.</span>
            <span className={blocks.muted}>
              A quality gate on mutation score, not just coverage, catches the exact failure mode line-coverage
              hides: tests that run the code but assert nothing meaningful.
            </span>
          </div>
          <div className={blocks.callout}>
            <span className={blocks.calloutTitle}>End-to-end, not a one-off script.</span>
            <span className={blocks.muted}>
              Analyze, gate and fix are the same engine calls whether they run on a laptop, this dashboard, or a CI
              runner — one measurement, everywhere it&rsquo;s asked for.
            </span>
          </div>
        </div>
      </Section>
    </PageShell>
  );
}
