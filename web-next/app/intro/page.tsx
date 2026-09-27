import type { Metadata } from "next";
import { SlideShell } from "../components/site/Page";
import { BrandMark } from "../components/site/Brand";
import styles from "./Intro.module.css";

export const metadata: Metadata = {
  title: "TestMind AI",
  description: "Multi-Agent QA Swarm powered by Vertex AI.",
};

export default function IntroPage() {
  return (
    <SlideShell>
      <div className={styles.hero}>
        <span className={styles.mark}>
          <BrandMark size={96} />
        </span>
        <h1 className={styles.name}>TestMind AI</h1>
        <p className={styles.tagline}>
          <strong>Multi-Agent QA Swarm powered by Vertex AI.</strong> Orchestrates Unit, API, and UI testing
          via MCP to autonomously detect gaps, fix tests, and ensure code quality.
        </p>
      </div>
    </SlideShell>
  );
}
