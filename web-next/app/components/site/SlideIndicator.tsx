"use client";

import { usePathname } from "next/navigation";
import { useDemoMode } from "../../context/DemoModeContext";
import { getSlideByPath } from "./links";
import styles from "./SlideIndicator.module.css";

export function SlideIndicator() {
  const { demoMode } = useDemoMode();
  const pathname = usePathname();

  if (!demoMode) {
    return null;
  }

  const slide = getSlideByPath(pathname);
  if (!slide) {
    return null;
  }

  return (
    <div className={styles.indicator} aria-label={`Slide ${slide.slideNumber} of 10: ${slide.slideTitle}`}>
      <span className={styles.badge}>Slide {String(slide.slideNumber).padStart(2, "0")} / 10</span>
      <span className={styles.divider}>·</span>
      <span className={styles.title}>{slide.slideTitle}</span>
    </div>
  );
}
