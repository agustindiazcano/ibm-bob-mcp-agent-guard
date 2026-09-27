import type { Metadata } from "next";
import { ButtonLink, PageHeader, PageShell, Section, Tag } from "../components/site/Page";
import { Icon } from "../components/site/Icon";
import blocks from "../components/site/Blocks.module.css";
import styles from "./security.module.css";

export const metadata: Metadata = {
  title: "Enterprise Security & Gate",
  description: "Workload Identity Federation (WIF), token-gated autofix, Docker, and Cloud Run production architecture.",
};

const SECURITY_PILLARS = [
  {
    title: "Keyless Workload Identity (WIF)",
    icon: "shield" as const,
    tag: "Production",
    text: "GitHub Actions assumes a Google Cloud Service Account via OIDC token federation. Zero stored service account keys in repository secrets.",
  },
  {
    title: "Airtight Write Guard",
    icon: "terminal" as const,
    tag: "Core Invariant",
    text: "AI agents cannot edit source files. The write tool strictly enforces a regex check allowing writes only under tests/. Any attempt throws SourceEditRejected.",
  },
  {
    title: "Token-Gated Autofix API",
    icon: "pipeline" as const,
    tag: "HTTP Security",
    text: "POST /api/fix requires a valid Bearer token from Secret Manager and enforces an in-memory lock to guarantee only one fix run runs at a time.",
  },
  {
    title: "Docker & Cloud Run Deployment",
    icon: "server" as const,
    tag: "Containerized",
    text: "Packaged via multi-stage Docker build, deployed on Google Cloud Run with autoscaling, IAM authentication, and Secret Manager environment wiring.",
  },
];

export default function SecurityGatePage() {
  return (
    <PageShell>
      <PageHeader
        eyebrow="Slide 09 · Platform"
        title="Enterprise Hardening, WIF & Cloud Run"
        lead="Phase 13 enterprise foundation: zero-trust identity federation, secretless deployment, hardened write-guards, and strict concurrency control for production deployments."
        actions={
          <>
            <ButtonLink href="/multicloud" variant="secondary">
              ← Slide 08: Multicloud AI
            </ButtonLink>
            <ButtonLink href="/data-platform" variant="primary">
              Next Slide: Data Platform →
            </ButtonLink>
          </>
        }
      />

      <Section
        title="Security & Governance Pillars"
        intro="Enterprise guardrails ensure that automated self-healing operates within strict compliance and infrastructure boundaries."
      >
        <div className={styles.pillarGrid}>
          {SECURITY_PILLARS.map((p) => (
            <div key={p.title} className={styles.pillarCard}>
              <div className={styles.pillarHead}>
                <div className={styles.pillarTitle}>
                  <Icon name={p.icon} />
                  <h3>{p.title}</h3>
                </div>
                <Tag tone="live">{p.tag}</Tag>
              </div>
              <p className={styles.pillarText}>{p.text}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section
        title="Terraform Infrastructure as Code"
        intro="Every cloud resource is codified in infra/terraform/ and validated on every commit with terraform fmt -check and validate."
      >
        <div className={blocks.grid}>
          <div className={blocks.item}>
            <div className={blocks.itemHead}>
              <Icon name="check" />
              <h3>Workload Identity Pool & Provider</h3>
            </div>
            <p>
              GitHub repository mapping is restricted to <code>attribute.repository == repo_name</code>, ensuring only
              authorized workflows can request temporary GCP access tokens.
            </p>
          </div>

          <div className={blocks.item}>
            <div className={blocks.itemHead}>
              <Icon name="trend" />
              <h3>Secret Manager Integration</h3>
            </div>
            <p>
              Sensitive runtime tokens like <code>REPOGUARD_FIX_TOKEN</code> and database credentials mount as
              versioned secrets directly into Cloud Run container volumes.
            </p>
          </div>

          <div className={blocks.item}>
            <div className={blocks.itemHead}>
              <Icon name="shield" />
              <h3>Immutable CI/CD Pipeline</h3>
            </div>
            <p>
              GitHub Actions runs phase determinism, regression tests, and quality gates before any deployment image
              is built or released to Artifact Registry.
            </p>
          </div>
        </div>
      </Section>
    </PageShell>
  );
}
