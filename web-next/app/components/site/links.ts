// Site links and slide configuration.
// Order follows the demo story:
// 1. Analyze (live measurement & fix loop)
// 2. Results (empirical metrics & history)
// 3. Features (what it does today, no more)
// 4. Anti-hallucination guardrails (G1-G6 + O1, real CI results)
// 5. Before/After code (real test files, not mock)
// 6. Tech stack (named technologies, grouped)
// 7. Built with IBM Bob (real commit/PR numbers)
// 8. Project (the core problem & why mutation testing matters)
// 9. Technical (deterministic architecture & FastMCP engine)
// 10. AI-Assisted Dev (safe file-contract framework)
// 11. Swarm (multi-agent parallel fix loop & sandboxes)
// 12. Mutation Engine (AST mutation & determinism)
// 13. Multicloud AI (Vertex AI Gemini & watsonx abstraction)
// 14. Enterprise Security (WIF, Secret Manager, Cloud Run)
// 15. Data Platform (PostgreSQL run history & analytical views)
// 16. Ship it (one-command install & CI/CD integration)

export type SiteLink = { href: string; label: string };

export type SlideInfo = {
  slideNumber: number;
  href: string;
  label: string;
  slideTitle: string;
  category: "Product" | "Architecture" | "Engine" | "Platform";
  description: string;
};

export const PRODUCT_LINKS: SiteLink[] = [
  { href: "/", label: "Analyze" },
  { href: "/results", label: "Results" },
];

export const ABOUT_LINKS: SiteLink[] = [
  { href: "/project", label: "Project" },
  { href: "/technical", label: "Technical" },
  { href: "/ai-development", label: "AI-assisted dev" },
];

export const DEMO_SLIDES: SlideInfo[] = [
  {
    slideNumber: 1,
    href: "/",
    label: "01",
    slideTitle: "Real-Time Analysis & Self-Healing AI",
    category: "Product",
    description: "Point TestMind AI at a repo to measure real test effectiveness with AST mutation testing and heal broken suites.",
  },
  {
    slideNumber: 2,
    href: "/results",
    label: "02",
    slideTitle: "Empirical Results & Quality Gate",
    category: "Product",
    description: "Coverage vs. mutation score history, surviving bug kinds, and verifiable deltas across runs.",
  },
  {
    slideNumber: 3,
    href: "/features",
    label: "03",
    slideTitle: "Features: What It Actually Does Today",
    category: "Product",
    description: "Mutation testing, self-healing tests, API checks, visual regression, risk ranking, quality gate — from the README, not a roadmap.",
  },
  {
    slideNumber: 4,
    href: "/hallucination-guardrails",
    label: "04",
    slideTitle: "Anti-Hallucination Guardrails (G1-G6 + O1)",
    category: "Engine",
    description: "What stops an LLM from cheating its own mutation score — seven guardrails, all green in CI.",
  },
  {
    slideNumber: 5,
    href: "/code-comparison",
    label: "05",
    slideTitle: "Before / After: Real Test Code",
    category: "Product",
    description: "The actual weak baseline vs. the reference suite for shop/pricing.py — real files from this repo.",
  },
  {
    slideNumber: 6,
    href: "/tech-stack",
    label: "06",
    slideTitle: "Tech Stack, Named",
    category: "Platform",
    description: "Python, watsonx.ai, Vertex AI, FastAPI, Next.js, GitHub Actions, Cloud Run, Terraform — grouped by layer.",
  },
  {
    slideNumber: 7,
    href: "/ibm-bob",
    label: "07",
    slideTitle: "Built With IBM Bob (Phases 0-8)",
    category: "Product",
    description: "12 commits, 820 lines, 1st of 6 on the team — Bob's real Bobalytics numbers, and what it built.",
  },
  {
    slideNumber: 8,
    href: "/project",
    label: "08",
    slideTitle: "The Problem: High Coverage, Broken Tests",
    category: "Architecture",
    description: "Why 80% line coverage often catches 0% of bugs, and how AST mutation testing measures truth.",
  },
  {
    slideNumber: 9,
    href: "/technical",
    label: "09",
    slideTitle: "Deterministic Architecture & FastMCP",
    category: "Architecture",
    description: "Layering rules, compact FastMCP tools, isolated subprocesses, and zero-stdout stdio protocol.",
  },
  {
    slideNumber: 10,
    href: "/ai-development",
    label: "10",
    slideTitle: "AI-Assisted Development Framework",
    category: "Architecture",
    description: "How TestMind AI itself is built: AI agents under file-based contracts checked against measured output.",
  },
  {
    slideNumber: 11,
    href: "/swarm",
    label: "11",
    slideTitle: "Multi-Agent Swarm & Parallel Sandboxes",
    category: "Engine",
    description: "One lane per file, temporary sandboxes outside target repo, and atomic blackboard coordination.",
  },
  {
    slideNumber: 12,
    href: "/mutation-engine",
    label: "12",
    slideTitle: "Deterministic AST Mutation Testing Engine",
    category: "Engine",
    description: "Stdlib AST mutations, comparison swaps, arithmetic inversions, and clean unmutated baseline gating.",
  },
  {
    slideNumber: 13,
    href: "/multicloud",
    label: "13",
    slideTitle: "Multicloud AI: Google Vertex AI & IBM watsonx",
    category: "Engine",
    description: "Unified ChatProvider abstraction, Gemini 3.8/3.5 Flash, Mistral 24B, and tool-calling write guards.",
  },
  {
    slideNumber: 14,
    href: "/security-gate",
    label: "14",
    slideTitle: "Enterprise Hardening, WIF & Cloud Run",
    category: "Platform",
    description: "Keyless Workload Identity Federation (WIF), Docker containers, Secret Manager, and CI/CD gates.",
  },
  {
    slideNumber: 15,
    href: "/data-platform",
    label: "15",
    slideTitle: "PostgreSQL Run History & Analytics Platform",
    category: "Platform",
    description: "SQLAlchemy 2 Core schema, portable view DDL for trends/flaky tests, and authenticated token ingest.",
  },
  {
    slideNumber: 16,
    href: "/pipeline",
    label: "16",
    slideTitle: "Ship It: One-Command Install & CI/CD Integration",
    category: "Product",
    description: "Real pip-installable package, verified live, dropping straight into any pipeline's quality gate and self-healing step.",
  },
];

export function getSlideByPath(pathname: string): SlideInfo | undefined {
  if (pathname === "/") {
    return DEMO_SLIDES[0];
  }
  return DEMO_SLIDES.find(
    (slide) => slide.href !== "/" && (pathname === slide.href || pathname.startsWith(`${slide.href}/`))
  );
}

export const REPO_URL = "https://github.com/agustindiazcano/ibm-bob-mcp-agent-guard";

export function repoDoc(path: string): string {
  return `${REPO_URL}/blob/main/${path}`;
}
