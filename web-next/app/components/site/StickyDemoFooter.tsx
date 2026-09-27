"use client";

import { useDemoMode } from "../../context/DemoModeContext";
import styles from "./StickyDemoFooter.module.css";

export function StickyDemoFooter() {
  const { demoMode } = useDemoMode();

  // Show only in Demo OFF mode as requested ("demo off nos muestra el sitio distinto, con un footer que esta siempre en el bottom de la pantalla...")
  if (demoMode) {
    return null;
  }

  return (
    <div className={styles.footer} role="contentinfo" aria-label="Demo Tech Stack & Team">
      <div className={styles.inner}>
        <div className={styles.stackSection}>
          <span className={styles.stackTitle}>Tech Stack:</span>
          <span className={`${styles.pill} ${styles.pillBob}`}>IBM Bob</span>
          <span className={`${styles.pill} ${styles.pillAccent}`}>watsonx.ai</span>
          <span className={`${styles.pill} ${styles.pillAccent}`}>Vertex AI</span>
          <span className={styles.pill}>Google Cloud</span>
          <span className={styles.pill}>FastAPI</span>
          <span className={styles.pill}>Python 3.10+</span>
          <span className={`${styles.pill} ${styles.pillGreen}`}>Full CI/CD (GitHub Actions + Cloud Run)</span>
        </div>
        <div className={styles.teamLine}>
          <span className={styles.teamFlag} aria-hidden="true">🇦🇷</span>
          <span>Team Argentina &middot; Agustin-Diaz-Cano</span>
        </div>
      </div>
    </div>
  );
}
