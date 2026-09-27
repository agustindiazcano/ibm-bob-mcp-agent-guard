"use client";

import { useDemoMode } from "../../context/DemoModeContext";
import styles from "./DemoSwitch.module.css";

export function DemoSwitch() {
  const { demoMode, toggleDemoMode } = useDemoMode();

  return (
    <div className={styles.container}>
      <button
        type="button"
        role="switch"
        aria-checked={demoMode}
        aria-label="Toggle demo mode"
        className={`${styles.switch} ${demoMode ? styles.switchOn : ""}`}
        onClick={toggleDemoMode}
      >
        <span className={styles.thumb} />
      </button>
      <span>Demo</span>
      <span className={`${styles.stateText} ${demoMode ? styles.stateTextOn : styles.stateTextOff}`}>
        {demoMode ? "ON" : "OFF"}
      </span>
    </div>
  );
}
