"use client";

import { useDemoMode } from "../../context/DemoModeContext";
import { TechStackPills } from "./TechStackPills";
import styles from "./StickyDemoFooter.module.css";

export function StickyDemoFooter() {
  const { demoMode } = useDemoMode();

  // Show only in Demo OFF mode as requested
  if (demoMode) {
    return null;
  }

  return (
    <div className={styles.footer} role="contentinfo" aria-label="Demo Tech Stack & Team">
      <div className={styles.inner}>
        <TechStackPills />

        <div className={styles.teamLine}>
          <span>
            Team Argentina &middot;{" "}
            <a
              href="https://www.agustindiazcano.com/"
              target="_blank"
              rel="noreferrer"
              className={styles.authorLink}
            >
              Agustin-Diaz-Cano
            </a>
          </span>
        </div>
      </div>
    </div>
  );
}
