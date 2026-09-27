import type { Metadata } from "next";
import { ButtonLink, SlideHeader, SlideShell } from "../components/site/Page";
import { REPO_URL } from "../components/site/links";
import blocks from "../components/site/Blocks.module.css";

export const metadata: Metadata = {
  title: "Ship it",
  description: "TestMind AI installs as a real Python package with one command and plugs straight into any CI/CD pipeline.",
};

const INSTALL = `pip install git+https://github.com/agustindiazcano/ibm-bob-mcp-agent-guard.git

repoguard analyze ./your-repo --mutation
repoguard gate ./your-repo --threshold 80
repoguard fix ./your-repo --publish`;

const CI_YAML = `- run: pip install "repoguard[vertex] @ git+https://github.com/agustindiazcano/ibm-bob-mcp-agent-guard.git"
- run: repoguard gate . --threshold 80          # fails the build if tests don't catch bugs
- run: repoguard fix . --publish                 # self-healing PR if the gate fails
  if: failure()`;

export default function PipelinePage() {
  return (
    <SlideShell>
      <SlideHeader
        eyebrow="Ship it"
        title="Not a demo app. A real package that drops into your CI/CD pipeline."
        lead="Verified live this session: pip install in a clean venv, then a real measurement against demo-repo with the same numbers as everywhere else."
      />
      <div className={blocks.grid2}>
        <div className={blocks.tile}>
          <h3 className={blocks.tileTitle}>Install & use</h3>
          <pre className={blocks.pre}>{INSTALL}</pre>
        </div>
        <div className={blocks.tile}>
          <h3 className={blocks.tileTitle}>Wire into any CI/CD pipeline</h3>
          <pre className={blocks.pre}>{CI_YAML}</pre>
        </div>
      </div>
      <ButtonLink href={REPO_URL} variant="secondary">
        View on GitHub
      </ButtonLink>
    </SlideShell>
  );
}
