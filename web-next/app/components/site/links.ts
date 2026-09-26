// One list for the nav and the footer, so a new screen is added in one place.
// Order follows the user flow: run a measurement, read the history, then
// the explainer pages.

export type SiteLink = { href: string; label: string };

export const PRODUCT_LINKS: SiteLink[] = [
  { href: "/", label: "Analyze" },
  { href: "/results", label: "Results" },
];

export const ABOUT_LINKS: SiteLink[] = [
  { href: "/project", label: "Project" },
  { href: "/technical", label: "Technical" },
  { href: "/ai-development", label: "AI-assisted dev" },
];

export const REPO_URL = "https://github.com/agustindiazcano/ibm-bob-mcp-agent-guard";

export function repoDoc(path: string): string {
  return `${REPO_URL}/blob/main/${path}`;
}
