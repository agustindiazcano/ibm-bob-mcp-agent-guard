// Small stroke icons for the explainer pages; decorative only.

const PATHS = {
  bug: "M9 9h6v8a3 3 0 0 1-6 0V9ZM10 6.5a2 2 0 0 1 4 0V9h-4V6.5ZM5 12h4M15 12h4M5.5 17.5 9 16M18.5 17.5 15 16M6 7l3 2M18 7l-3 2",
  tests: "M9 6h10M9 12h10M9 18h10M4.5 6l1 1 2-2M4.5 12l1 1 2-2M4.5 18l1 1 2-2",
  api: "M8 7 3 12l5 5M16 7l5 5-5 5M13.5 5l-3 14",
  eye: "M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12ZM12 14.75a2.75 2.75 0 1 0 0-5.5 2.75 2.75 0 0 0 0 5.5Z",
  risk: "M4 20V10M10 20V4M16 20v-7M22 20H2",
  terminal: "M4 5h16v14H4zM7.5 9.5l3 2.5-3 2.5M12.5 15h4",
  globe: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18ZM3 12h18M12 3c2.5 2.7 3.5 5.7 3.5 9s-1 6.3-3.5 9c-2.5-2.7-3.5-5.7-3.5-9s1-6.3 3.5-9Z",
  plug: "M9 3v5M15 3v5M6 8h12v3a6 6 0 0 1-12 0V8ZM12 17v4",
  shield: "M12 3 5 6v5.5c0 4.3 3 7.9 7 9.5 4-1.6 7-5.2 7-9.5V6l-7-3ZM9 12l2 2 4-4",
  check: "M20 6 9 17l-5-5",
  trend: "m22 7-8.5 8.5-5-5L2 17M16 7h6v6",
  pipeline: "M5 12h14M12 5l7 7-7 7M5 6v12",
  server: "M4 4h16v6H4zm0 10h16v6H4zm4-7h.01M8 17h.01",
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({ name }: { name: IconName }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="20"
      height="20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
