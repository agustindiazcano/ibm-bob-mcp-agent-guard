import Link from "next/link";
import styles from "./Brand.module.css";

export function Brand() {
  return (
    <Link href="/" className={styles.brand} aria-label="TestMind AI, home">
      <svg className={styles.mark} viewBox="0 0 28 28" aria-hidden="true">
        <rect width="28" height="28" rx="7" className={styles.markBg} />
        <path d="M8 14.5l4 4 8-9" className={styles.markCheck} />
        <circle cx="20.5" cy="19.5" r="2.25" className={styles.markDot} />
      </svg>
      <span className={styles.name}>TestMind AI</span>
    </Link>
  );
}

export function BobBadge({ size = "md" }: { size?: "sm" | "md" }) {
  return (
    <span className={`${styles.badge} ${size === "sm" ? styles.badgeSm : ""}`}>
      <span className={styles.badgeDot} aria-hidden="true" />
      IBM Bob 2.0
    </span>
  );
}
