import type { Metadata } from "next";
import type { ReactNode } from "react";
import { PageHeader, PageShell, Section, Tag } from "../components/site/Page";
import { repoDoc } from "../components/site/links";
import blocks from "../components/site/Blocks.module.css";
import styles from "./technical.module.css";

export const metadata: Metadata = {
  title: "Technical",
  description: "Architecture, mutation engine, AI fix loop, HTTP API and deployment of TestMind AI.",
};

type Box = { name: string; detail: string; accent?: boolean };

const TIERS: { label: string; boxes: Box[] }[] = [
  {
    label: "Entry points",
    boxes: [
      { name: "Terminal", detail: "repoguard analyze · fix · gate" },
      { name: "Web", detail: "Next.js on Vercel → FastAPI on Cloud Run (HTTP, SSE, NDJSON)" },
      { name: "MCP client", detail: "repoguard mcp · 9 tools over stdio" },
    ],
  },
  {
    label: "Orchestration",
    boxes: [
      { name: "pipeline.py", detail: "Runs the measurement steps in order, returns one result" },
      { name: "watson_agent/", detail: "Fix loop: measure → write → critique → re-measure", accent: true },
    ],
  },
  {
    label: "Engine (deterministic)",
    boxes: [
      { name: "core.py", detail: "pytest, coverage, AST mutation, gaps, risk" },
      { name: "api_check.py", detail: "FastAPI routes by AST, endpoint smoke tests" },
      { name: "visual.py", detail: "Screenshots, pixel diff, console, accessibility" },
      { name: "ai_providers/", detail: "watsonx.ai · Vertex AI, behind one ChatProvider", accent: true },
    ],
  },
  {
    label: "Outputs",
    boxes: [
      { name: "repoguard-out/*.json", detail: "The contract between agents: every step writes its result here" },
      { name: "Target repo", detail: "Read for measurement; agents may write under tests/ only" },
    ],
  },
];

const OPERATORS: { name: string; change: string; catches: string }[] = [
  { name: "Comparison", change: "== ↔ !=, < ↔ >=, > ↔ <=", catches: "Off-by-one and boundary bugs" },
  { name: "Arithmetic", change: "+ ↔ -, * ↔ /", catches: "Wrong formula, sign errors" },
  { name: "Boolean", change: "and ↔ or", catches: "Wrong condition logic" },
  { name: "Constants", change: "True ↔ False, n → n + 1", catches: "Magic numbers, flags" },
  { name: "Return", change: "return x → return None", catches: "Results nobody asserts on" },
  { name: "Raise", change: "raise … removed", catches: "Error paths with no test" },
];

const GUARDS: { title: string; text: ReactNode }[] = [
  {
    title: "Baseline must pass first",
    text: "Before mutating anything, the unmodified suite has to pass. Otherwise every mutant would count as killed and a broken suite would score 100%.",
  },
  {
    title: "Same repo in, same numbers out",
    text: (
      <>
        Each mutant runs on a temporary copy with <code>PYTHONDONTWRITEBYTECODE=1</code>, so stale bytecode can&rsquo;t
        leak between runs. Two runs on demo-repo give 16/79 both times.
      </>
    ),
  },
  {
    title: "Pinned interpreter",
    text: (
      <>
        Every pytest subprocess runs through <code>sys.executable</code>, never a bare <code>pytest</code> on PATH that
        could resolve to a different environment.
      </>
    ),
  },
  {
    title: "Write guard",
    text: (
      <>
        The fix loop&rsquo;s only write tool, <code>write_test_file</code>, rejects any path outside <code>tests/</code>.
        Autofix over HTTP also runs on a copy of the repo, so the original is never touched.
      </>
    ),
  },
  {
    title: "Fail loud, never fake",
    text: "A check that couldn't run returns ok=false with the real error (missing credentials, missing dependency) instead of an empty result that looks like a pass.",
  },
];

const ENDPOINTS: { method: string; path: string; what: string; tag?: string }[] = [
  { method: "GET", path: "/api/analyze", what: "Runs the pipeline: coverage, gaps, risk, optional mutation and gate" },
  { method: "GET", path: "/api/stream", what: "Server-sent events with live progress for the same run" },
  { method: "POST", path: "/api/summary", what: "Advisory AI prose over an already-measured result, plus the provider used" },
  { method: "POST", path: "/api/fix", what: "Autofix: bearer token, one run at a time, NDJSON progress and engine before/after" },
  { method: "GET", path: "/api/projects/{slug}/…", what: "Run history for the Results charts: trend, operators, risk, fix effect, survivors, flaky", tag: "Phase 17" },
];

const STACK: [string, string][] = [
  ["Python", "≥ 3.10"],
  ["pytest", "+ coverage.py"],
  ["ast", "own mutation engine"],
  ["FastAPI", "+ uvicorn, SSE"],
  ["MCP", "Python SDK, stdio"],
  ["Playwright", "+ Pillow, axe"],
  ["watsonx.ai", "default provider"],
  ["Vertex AI", "Gemini"],
  ["Next.js", "16 · React 19"],
  ["Docker", "Cloud Run"],
  ["GitHub Actions", "CI/CD"],
  ["Terraform", "WIF identity"],
];

export default function TechnicalPage() {
  return (
    <PageShell>
      <PageHeader
        eyebrow="Technical"
        title="One deterministic engine, three thin adapters."
        lead="The engine measures and writes JSON; the CLI, the web API and the MCP server only call it. The AI layer sits beside the engine, never inside a measurement."
      />

      <Section
        id="architecture"
        title="Architecture"
        intro="Layering is a rule, not a preference: core.py has no web, MCP or CLI code, and every adapter goes through pipeline.py or core.py."
      >
        <div className={styles.diagram} role="img" aria-label="Architecture: entry points call orchestration, which calls the engine, which writes outputs">
          {TIERS.map((tier, i) => (
            <div key={tier.label} className={styles.tierWrap}>
              {i > 0 && <span className={styles.connector} aria-hidden="true" />}
              <div className={styles.tier}>
                <span className={styles.tierLabel}>{tier.label}</span>
                <div className={styles.tierBoxes}>
                  {tier.boxes.map((b) => (
                    <div key={b.name} className={`${styles.box} ${b.accent ? styles.boxAi : ""}`}>
                      <code className={styles.boxName}>{b.name}</code>
                      <span className={styles.boxDetail}>{b.detail}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
        <p className={styles.legend}>
          <span className={styles.legendSwatch} aria-hidden="true" /> AI components. Everything else is deterministic.
        </p>
      </Section>

      <Section
        id="mutation"
        title="Mutation engine"
        intro="Written on the standard library's ast module (no mutmut or Stryker). It changes one node at a time, reruns the suite on a copy, and counts the mutants no test notices."
      >
        <div className={blocks.tableWrap}>
          <table className={blocks.table}>
            <thead>
              <tr>
                <th scope="col">Operator</th>
                <th scope="col">Change</th>
                <th scope="col">Catches missing tests for</th>
              </tr>
            </thead>
            <tbody>
              {OPERATORS.map((o) => (
                <tr key={o.name}>
                  <td>{o.name}</td>
                  <td>
                    <code>{o.change}</code>
                  </td>
                  <td>{o.catches}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section id="guardrails" title="Guardrails that keep the numbers honest">
        <div className={blocks.grid3}>
          {GUARDS.map((g) => (
            <div key={g.title} className={blocks.tile}>
              <h3 className={blocks.tileTitle}>{g.title}</h3>
              <p className={blocks.tileText}>{g.text}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section
        id="fix-loop"
        title="AI fix loop"
        intro="repoguard fix and the Autofix button run the same loop, in-process against the engine rather than through MCP."
      >
        <div className={blocks.grid2}>
          <ol className={styles.loop}>
            <li>
              <strong>Measure.</strong> Full pipeline with mutation and endpoints.
            </li>
            <li>
              <strong>Prioritize.</strong> Up to 3 files, by the engine&rsquo;s risk score.
            </li>
            <li>
              <strong>Write.</strong> The test-writer agent reads the source and writes a test through the guarded tool, and
              must run pytest before it finishes.
            </li>
            <li>
              <strong>Critique.</strong> A second agent with its own prompt reviews and corrects the test.
            </li>
            <li>
              <strong>Re-measure.</strong> The engine measures again; the report goes to <code>watson-evidence/</code>.
            </li>
          </ol>
          <div className={blocks.tableWrap}>
            <table className={blocks.table}>
              <thead>
                <tr>
                  <th scope="col">Provider</th>
                  <th scope="col">Select with</th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>IBM watsonx.ai</td>
                  <td>
                    <code>REPOGUARD_AI_PROVIDER=watsonx</code> (default)
                  </td>
                  <td>
                    <Tag tone="live">Live-verified</Tag>
                    <span className={styles.note}>The default model calls tools unreliably</span>
                  </td>
                </tr>
                <tr>
                  <td>Google Vertex AI</td>
                  <td>
                    <code>REPOGUARD_AI_PROVIDER=vertex</code>
                  </td>
                  <td>
                    <Tag tone="live">Live-verified</Tag>
                    <span className={styles.note}>Gemini 3: 20.25% → 89.87% on demo-repo</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </Section>

      <Section id="api" title="HTTP API" intro="What this dashboard calls. The backend is repoguard_engine/web/server.py.">
        <div className={blocks.tableWrap}>
          <table className={blocks.table}>
            <thead>
              <tr>
                <th scope="col">Method</th>
                <th scope="col">Path</th>
                <th scope="col">Does</th>
              </tr>
            </thead>
            <tbody>
              {ENDPOINTS.map((e) => (
                <tr key={e.path} className={e.tag ? styles.plannedRow : undefined}>
                  <td>
                    <span className={styles.method}>{e.method}</span>
                  </td>
                  <td>
                    <code>{e.path}</code>
                  </td>
                  <td>
                    {e.what} {e.tag && <Tag tone="planned">{e.tag}</Tag>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section id="deploy" title="Deployment and CI">
        <div className={blocks.grid3}>
          <div className={blocks.tile}>
            <h3 className={blocks.tileTitle}>Frontend</h3>
            <p className={blocks.tileText}>
              <code>web-next/</code> on Vercel; every merge to <code>main</code> redeploys. The backend URL is baked in at
              build time through <code>NEXT_PUBLIC_REPOGUARD_API_BASE</code>.
            </p>
          </div>
          <div className={blocks.tile}>
            <h3 className={blocks.tileTitle}>Backend</h3>
            <p className={blocks.tileText}>
              Docker image on Google Cloud Run, pushed by <code>cd.yml</code> through Workload Identity Federation (no
              stored keys). The identity is managed in Terraform.
            </p>
          </div>
          <div className={blocks.tile}>
            <h3 className={blocks.tileTitle}>Checks</h3>
            <p className={blocks.tileText}>
              <code>ci.yml</code> re-measures demo-repo and checks determinism; <code>frontend-ci.yml</code> lints and
              builds this app; <code>infra-ci.yml</code> validates Terraform.
            </p>
          </div>
        </div>
      </Section>

      <Section id="stack" title="Stack">
        <div className={blocks.chips}>
          {STACK.map(([name, note]) => (
            <span key={name} className={blocks.chip}>
              <strong>{name}</strong> <span>{note}</span>
            </span>
          ))}
        </div>
        <p className={blocks.muted}>
          Deeper reading:{" "}
          <a href={repoDoc("docs/ARCHITECTURE.md")} target="_blank" rel="noreferrer">
            ARCHITECTURE.md
          </a>{" "}
          ·{" "}
          <a href={repoDoc("docs/ARCHITECTURE-front.md")} target="_blank" rel="noreferrer">
            ARCHITECTURE-front.md
          </a>{" "}
          ·{" "}
          <a href={repoDoc("docs/MULTICLOUD_AI.md")} target="_blank" rel="noreferrer">
            MULTICLOUD_AI.md
          </a>
        </p>
      </Section>
    </PageShell>
  );
}
