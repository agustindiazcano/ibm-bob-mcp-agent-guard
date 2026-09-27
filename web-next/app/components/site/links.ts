// Site links and slide configuration.
// Order follows the demo story:
// 1. Analyze (live measurement & fix loop)
// 2. Results (empirical metrics & history)
// 3. Project (the core problem & why mutation testing matters)
// 4. Technical (deterministic architecture & FastMCP engine)
// 5. AI-Assisted Dev (safe file-contract framework)
// 6. Swarm (multi-agent parallel fix loop & sandboxes)
// 7. Mutation Engine (AST mutation & determinism)
// 8. Multicloud AI (Vertex AI Gemini & watsonx abstraction)
// 9. Enterprise Security (WIF, Secret Manager, Cloud Run)
// 10. Data Platform (PostgreSQL run history & analytical views)

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
    href: "/project",
    label: "03",
    slideTitle: "The Problem: High Coverage, Broken Tests",
    category: "Architecture",
    description: "Why 80% line coverage often catches 0% of bugs, and how AST mutation testing measures truth.",
  },
  {
    slideNumber: 4,
    href: "/technical",
    label: "04",
    slideTitle: "Deterministic Architecture & FastMCP",
    category: "Architecture",
    description: "Layering rules, compact FastMCP tools, isolated subprocesses, and zero-stdout stdio protocol.",
  },
  {
    slideNumber: 5,
    href: "/ai-development",
    label: "05",
    slideTitle: "AI-Assisted Development Framework",
    category: "Architecture",
    description: "How TestMind AI itself is built: AI agents under file-based contracts checked against measured output.",
  },
  {
    slideNumber: 6,
    href: "/swarm",
    label: "06",
    slideTitle: "Multi-Agent Swarm & Parallel Sandboxes",
    category: "Engine",
    description: "One lane per file, temporary sandboxes outside target repo, and atomic blackboard coordination.",
  },
  {
    slideNumber: 7,
    href: "/mutation-engine",
    label: "07",
    slideTitle: "Deterministic AST Mutation Testing Engine",
    category: "Engine",
    description: "Stdlib AST mutations, comparison swaps, arithmetic inversions, and clean unmutated baseline gating.",
  },
  {
    slideNumber: 8,
    href: "/multicloud",
    label: "08",
    slideTitle: "Multicloud AI: Google Vertex AI & IBM watsonx",
    category: "Engine",
    description: "Unified ChatProvider abstraction, Gemini 3.8/3.5 Flash, Mistral 24B, and tool-calling write guards.",
  },
  {
    slideNumber: 9,
    href: "/security-gate",
    label: "09",
    slideTitle: "Enterprise Hardening, WIF & Cloud Run",
    category: "Platform",
    description: "Keyless Workload Identity Federation (WIF), Docker containers, Secret Manager, and CI/CD gates.",
  },
  {
    slideNumber: 10,
    href: "/data-platform",
    label: "10",
    slideTitle: "PostgreSQL Run History & Analytics Platform",
    category: "Platform",
    description: "SQLAlchemy 2 Core schema, portable view DDL for trends/flaky tests, and authenticated token ingest.",
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
