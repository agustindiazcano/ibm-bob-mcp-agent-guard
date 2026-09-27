// Site links and slide configuration.
// Order follows the demo story:
// 0. Intro (logo + one-line pitch, the deck's cover)
// 1. Analyze (live measurement & fix loop)
// 2. Results (empirical metrics & history)
// 3. Features (what it does today, no more)
// 4. Features 2 (everything else that's real, incl. the honest "partial")
// 5. Anti-hallucination guardrails (G1-G6 + O1, real CI results)
// 6. Ship it (one-command install & CI/CD integration)
// 7. Tech stack (named technologies, grouped)
// 8. Built with IBM Bob (real commit/PR numbers + the AI-assisted handoff)
// 9. Swarm (multi-agent parallel fix loop & sandboxes)
// 10. Multicloud AI (Vertex AI Gemini & watsonx abstraction)
//
// Kept as pages, not in this deck: /project, /technical, /ai-development,
// /mutation-engine, /security-gate, /data-platform. /code-comparison was
// removed entirely (not just hidden).

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
    slideNumber: 0,
    href: "/intro",
    label: "00",
    slideTitle: "TestMind AI",
    category: "Product",
    description: "Multi-Agent QA Swarm powered by Vertex AI — orchestrates Unit, API, and UI testing via MCP.",
  },
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
    href: "/features-2",
    label: "04",
    slideTitle: "Features 2: Everything Else That's Real",
    category: "Product",
    description: "MCP server, multicloud AI, guardrails, write guard, enterprise infra, charts, and Swarm (the one honestly marked partial).",
  },
  {
    slideNumber: 5,
    href: "/hallucination-guardrails",
    label: "05",
    slideTitle: "Anti-Hallucination Guardrails (G1-G6 + O1)",
    category: "Engine",
    description: "What stops an LLM from cheating its own mutation score — seven guardrails, all green in CI.",
  },
  {
    slideNumber: 6,
    href: "/pipeline",
    label: "06",
    slideTitle: "Ship It: One-Command Install & CI/CD Integration",
    category: "Product",
    description: "Real pip-installable package, verified live, dropping straight into any pipeline's quality gate and self-healing step.",
  },
  {
    slideNumber: 7,
    href: "/tech-stack",
    label: "07",
    slideTitle: "Tech Stack, Named",
    category: "Platform",
    description: "Python, watsonx.ai, Vertex AI, FastAPI, Next.js, GitHub Actions, Cloud Run, Terraform — grouped by layer.",
  },
  {
    slideNumber: 8,
    href: "/ibm-bob",
    label: "08",
    slideTitle: "Built With IBM Bob (Phases 0-8)",
    category: "Product",
    description: "12 commits, 4 PRs, 1st of 6 on the team — Bob's real Bobalytics numbers, and the AI-assisted flow that took over from there.",
  },
  {
    slideNumber: 9,
    href: "/swarm",
    label: "09",
    slideTitle: "Multi-Agent Swarm & Parallel Sandboxes",
    category: "Engine",
    description: "One lane per file, temporary sandboxes outside target repo, and atomic blackboard coordination.",
  },
  {
    slideNumber: 10,
    href: "/multicloud",
    label: "10",
    slideTitle: "Multicloud AI: Google Vertex AI & IBM watsonx",
    category: "Engine",
    description: "Unified ChatProvider abstraction, Gemini 3.8/3.5 Flash, Mistral 24B, and tool-calling write guards.",
  },
];

export function getSlideByPath(pathname: string): SlideInfo | undefined {
  return DEMO_SLIDES.find(
    (slide) => pathname === slide.href || (slide.href !== "/" && pathname.startsWith(`${slide.href}/`))
  );
}

export const REPO_URL = "https://github.com/agustindiazcano/ibm-bob-mcp-agent-guard";

export function repoDoc(path: string): string {
  return `${REPO_URL}/blob/main/${path}`;
}
