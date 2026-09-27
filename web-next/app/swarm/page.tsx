import type { Metadata } from "next";
import { ButtonLink, PageHeader, PageShell, Section, Tag } from "../components/site/Page";
import { Icon } from "../components/site/Icon";
import blocks from "../components/site/Blocks.module.css";
import styles from "./swarm.module.css";

export const metadata: Metadata = {
  title: "Multi-Agent Swarm",
  description: "Phase 18 Swarm: isolated per-file repair lanes running in parallel sandboxes outside the target repo.",
};

const SWARM_LANES = [
  {
    file: "shop/cart.py",
    sandbox: "/tmp/swarm_lane_cart_a9f1",
    status: "ACCEPTED",
    testsGenerated: 4,
    mutantsKilled: 8,
    executionTime: "14.2s",
    gain: "+22.5% mutation score",
  },
  {
    file: "shop/pricing.py",
    sandbox: "/tmp/swarm_lane_pricing_7c3b",
    status: "ACCEPTED",
    testsGenerated: 6,
    mutantsKilled: 12,
    executionTime: "18.6s",
    gain: "+31.2% mutation score",
  },
  {
    file: "shop/inventory.py",
    sandbox: "/tmp/swarm_lane_inventory_2e0d",
    status: "ACCEPTED",
    testsGenerated: 3,
    mutantsKilled: 5,
    executionTime: "11.8s",
    gain: "+14.0% mutation score",
  },
  {
    file: "shop/api.py",
    sandbox: "/tmp/swarm_lane_api_44a2",
    status: "ACCEPTED",
    testsGenerated: 7,
    mutantsKilled: 15,
    executionTime: "22.4s",
    gain: "+38.0% mutation score",
  },
];

export default function SwarmPage() {
  return (
    <PageShell>
      <PageHeader
        eyebrow="Slide 06 · Engine"
        title="Multi-Agent Swarm & Parallel Sandboxes"
        lead="Phase 18 multi-agent fix loop: breaks repo repair into isolated lanes per source file. Each lane operates in a pristine temporary sandbox outside the workspace, coordinating through atomic blackboard contracts."
        actions={
          <>
            <ButtonLink href="/" variant="primary">
              Run Live Analyze
            </ButtonLink>
            <ButtonLink href="/mutation-engine" variant="secondary">
              Next Slide: AST Mutation Engine →
            </ButtonLink>
          </>
        }
      />

      <Section
        title="Parallel Lane Execution Matrix"
        intro="Lanes run concurrently across independent thread workers. Each lane only writes to tests/ inside its isolated sandbox, verifying pytest and scoped mutation before merging."
      >
        <div className={styles.lanesGrid}>
          {SWARM_LANES.map((lane) => (
            <div key={lane.file} className={styles.laneCard}>
              <div className={styles.laneHead}>
                <div className={styles.laneFile}>
                  <Icon name="tests" />
                  <span>{lane.file}</span>
                </div>
                <Tag tone="live">{lane.status}</Tag>
              </div>

              <div className={styles.sandboxPath}>
                <code>{lane.sandbox}</code>
              </div>

              <div className={styles.laneStats}>
                <div className={styles.laneStat}>
                  <span className={styles.statLabel}>Tests Created</span>
                  <span className={styles.statValue}>+{lane.testsGenerated}</span>
                </div>
                <div className={styles.laneStat}>
                  <span className={styles.statLabel}>Mutants Killed</span>
                  <span className={styles.statValue}>{lane.mutantsKilled}</span>
                </div>
                <div className={styles.laneStat}>
                  <span className={styles.statLabel}>Wall Time</span>
                  <span className={styles.statValue}>{lane.executionTime}</span>
                </div>
              </div>

              <div className={styles.laneGain}>
                <span className={styles.gainBadge}>{lane.gain}</span>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section
        title="Architecture Guardrails"
        intro="The Swarm architecture enforces strict safety guarantees to prevent runaway edits or cross-lane corruption."
      >
        <div className={blocks.grid}>
          <div className={blocks.item}>
            <div className={blocks.itemHead}>
              <Icon name="shield" />
              <h3>Complete Sandbox Isolation</h3>
            </div>
            <p>
              Each lane is cloned into an ephemeral directory outside the repo tree. File writes are physically
              isolated, and sandboxes are cleaned up automatically upon exit.
            </p>
          </div>

          <div className={blocks.item}>
            <div className={blocks.itemHead}>
              <Icon name="terminal" />
              <h3>Strict Write Guard</h3>
            </div>
            <p>
              Agents have access to a single write tool that rejects any path outside <code>tests/</code>. Source code
              is immutable reference truth; passing tests can never be forged by altering source.
            </p>
          </div>

          <div className={blocks.item}>
            <div className={blocks.itemHead}>
              <Icon name="pipeline" />
              <h3>Atomic Blackboard Contract</h3>
            </div>
            <p>
              Subagents share no memory. All communication happens via schema-tagged atomic JSON and snapshot files
              under <code>repoguard-out/swarm/&lt;run_id&gt;/</code>.
            </p>
          </div>
        </div>
      </Section>
    </PageShell>
  );
}
