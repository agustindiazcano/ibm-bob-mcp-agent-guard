// Published demo-repo numbers quoted on the explainer pages. Copied from
// CLAUDE.md §7 / README.md "Results on the bundled demo repo", which
// scripts/verify.py re-measures. Nothing here is computed in the browser:
// if a re-measurement changes a number there, update it here in the same PR.

export type BeforeAfter = {
  label: string;
  before: string;
  after: string;
  detail?: string;
  emphasis?: boolean;
};

export const DEMO_REPO_RESULTS: BeforeAfter[] = [
  {
    label: "Bugs caught (mutation score)",
    before: "20.25%",
    after: "89.87%",
    detail: "16 / 79 → 71 / 79 mutants killed",
    emphasis: true,
  },
  { label: "Line coverage", before: "65.1%", after: "100%", detail: "What most dashboards stop at" },
  { label: "Tests", before: "5", after: "71", detail: "Passing, against unmodified source" },
  { label: "API endpoints with a test", before: "1 of 7", after: "7 of 7", detail: "Found by parsing FastAPI routes" },
];
