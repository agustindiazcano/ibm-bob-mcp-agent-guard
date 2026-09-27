import type { Metadata } from "next";
import { SlideHeader, SlideShell } from "../components/site/Page";
import blocks from "../components/site/Blocks.module.css";

export const metadata: Metadata = {
  title: "Tech Stack",
  description: "Every real technology behind TestMind AI, grouped by layer — from the README's tech-stack table.",
};

const GROUPS: { label: string; items: string[] }[] = [
  { label: "Engine & testing", items: ["Python 3.10+", "pytest", "coverage.py", "stdlib ast (own engine)"] },
  { label: "Multicloud AI", items: ["IBM watsonx.ai", "Google Vertex AI · Gemini 3.8/3.5", "ChatProvider abstraction"] },
  { label: "API, protocol & frontend", items: ["FastAPI", "MCP (FastMCP) · 9 tools", "Next.js 16", "React 19", "TypeScript 5"] },
  { label: "Visual & accessibility", items: ["Playwright + Chromium", "Pillow", "axe-core"] },
  { label: "Data", items: ["PostgreSQL 16 (Cloud SQL)", "SQLite", "SQLAlchemy 2 Core"] },
  { label: "CI/CD & cloud", items: ["GitHub Actions", "Docker", "Google Cloud Run", "Vercel", "Terraform", "Workload Identity Federation"] },
];

export default function TechStackPage() {
  return (
    <SlideShell>
      <SlideHeader
        eyebrow="Stack"
        title="One engine, real infrastructure — not a prototype held together with scripts."
        lead="Every item here runs in this repo today (README's tech-stack table has the exact verification status per row)."
      />
      <div className={blocks.grid3}>
        {GROUPS.map((g) => (
          <div key={g.label} className={blocks.tile}>
            <h3 className={blocks.tileTitle}>{g.label}</h3>
            <div className={blocks.chips}>
              {g.items.map((item) => (
                <span key={item} className={blocks.chip}>
                  <strong>{item}</strong>
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </SlideShell>
  );
}
