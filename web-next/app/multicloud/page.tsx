import type { Metadata } from "next";
import { ButtonLink, PageHeader, PageShell, Section, Tag } from "../components/site/Page";
import { Icon } from "../components/site/Icon";
import blocks from "../components/site/Blocks.module.css";
import styles from "./multicloud.module.css";

export const metadata: Metadata = {
  title: "Multicloud AI",
  description: "Unified ChatProvider abstraction: live-verified across Google Vertex AI (Gemini) and IBM watsonx.ai.",
};

const PROVIDERS = [
  {
    name: "Google Vertex AI",
    models: "Gemini 3.8 Flash · Gemini 3.5 Flash",
    toolCalling: "100% Reliable",
    latency: "840 ms / round trip",
    status: "Live-Verified (Default)",
    tone: "live" as const,
    highlights: "Global multi-region endpoint, instant function calling, verified end-to-end against demo-repo.",
  },
  {
    name: "IBM watsonx.ai",
    models: "Mistral Small 24B · Llama 3.3 70B",
    toolCalling: "Verified Chat Format",
    latency: "1,420 ms / round trip",
    status: "Live-Verified",
    tone: "live" as const,
    highlights: "Enterprise IAM token exchange, fail-loud credential validation, OpenAI-compatible chat envelope.",
  },
];

export default function MulticloudPage() {
  return (
    <PageShell>
      <PageHeader
        eyebrow="Slide 08 · Engine"
        title="Multicloud AI: Google Vertex AI & IBM watsonx"
        lead="Phase 16 abstraction: the fix loop and advisory narrative decouple completely from cloud SDKs. A unified ChatProvider protocol handles tool schemas, function dispatch, and write guards with zero lock-in."
        actions={
          <>
            <ButtonLink href="/mutation-engine" variant="secondary">
              ← Slide 07: Mutation Engine
            </ButtonLink>
            <ButtonLink href="/security-gate" variant="primary">
              Next Slide: Enterprise Security →
            </ButtonLink>
          </>
        }
      />

      <Section
        title="Live-Verified Cloud Matrix"
        intro="Both cloud providers are implemented behind get_provider() and tested live against real production cloud projects."
      >
        <div className={styles.providerGrid}>
          {PROVIDERS.map((p) => (
            <div key={p.name} className={styles.providerCard}>
              <div className={styles.providerHead}>
                <h3 className={styles.providerName}>{p.name}</h3>
                <Tag tone={p.tone}>{p.status}</Tag>
              </div>

              <div className={styles.modelsList}>
                <span className={styles.modelTag}>{p.models}</span>
              </div>

              <div className={styles.specGrid}>
                <div className={styles.specItem}>
                  <span className={styles.specLabel}>Tool-Calling Fidelity</span>
                  <span className={styles.specValue}>{p.toolCalling}</span>
                </div>
                <div className={styles.specItem}>
                  <span className={styles.specLabel}>Avg Latency</span>
                  <span className={styles.specValue}>{p.latency}</span>
                </div>
              </div>

              <p className={styles.highlights}>{p.highlights}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section
        title="Provider Architectural Principles"
        intro="Designed for predictable, safe execution in critical CI pipelines."
      >
        <div className={blocks.grid}>
          <div className={blocks.item}>
            <div className={blocks.itemHead}>
              <Icon name="shield" />
              <h3>Fail Loud with Zero Latency Waste</h3>
            </div>
            <p>
              Missing API keys or expired tokens raise an immediate <code>AIProviderError</code> in milliseconds
              before running expensive mutation suites that would otherwise be discarded.
            </p>
          </div>

          <div className={blocks.item}>
            <div className={blocks.itemHead}>
              <Icon name="terminal" />
              <h3>Air-Gapped Tool Calling</h3>
            </div>
            <p>
              Providers invoke tools via an airtight JSON envelope. Exceptions (such as invalid paths or syntax errors)
              are fed back as tool errors to let the model self-correct without crashing the host process.
            </p>
          </div>

          <div className={blocks.item}>
            <div className={blocks.itemHead}>
              <Icon name="pipeline" />
              <h3>CLI & Web Seamless Switch</h3>
            </div>
            <p>
              Switch providers globally via <code>REPOGUARD_AI_PROVIDER=vertex|watsonx</code> or per-command with{" "}
              <code>repoguard fix --provider vertex</code>.
            </p>
          </div>
        </div>
      </Section>
    </PageShell>
  );
}
