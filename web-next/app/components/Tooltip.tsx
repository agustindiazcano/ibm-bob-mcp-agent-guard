"use client";

import type { ReactNode } from "react";
import styles from "./Tooltip.module.css";

type Props = {
  content: ReactNode;
  ariaLabel?: string;
};

export function Tooltip({ content, ariaLabel = "More information" }: Props) {
  return (
    <span className={styles.wrapper}>
      <button
        type="button"
        className={styles.trigger}
        aria-label={ariaLabel}
        tabIndex={0}
      >
        ?
      </button>
      <span className={styles.popover} role="tooltip">
        {content}
      </span>
    </span>
  );
}
