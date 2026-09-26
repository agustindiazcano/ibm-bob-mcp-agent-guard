import Link from "next/link";
import type { ReactNode } from "react";
import styles from "./Page.module.css";

// Layout primitives for the explainer pages (/project, /technical,
// /ai-development) and the /results shell. Presentation only.

export function PageShell({ children }: { children: ReactNode }) {
  return <main className={styles.shell}>{children}</main>;
}

type HeaderProps = {
  eyebrow: string;
  title: ReactNode;
  lead: ReactNode;
  actions?: ReactNode;
};

export function PageHeader({ eyebrow, title, lead, actions }: HeaderProps) {
  return (
    <header className={styles.header}>
      <span className={styles.eyebrow}>{eyebrow}</span>
      <h1 className={styles.title}>{title}</h1>
      <p className={styles.lead}>{lead}</p>
      {actions && <div className={styles.actions}>{actions}</div>}
    </header>
  );
}

type SectionProps = {
  id?: string;
  title: string;
  intro?: ReactNode;
  children: ReactNode;
};

export function Section({ id, title, intro, children }: SectionProps) {
  return (
    <section id={id} className={styles.section} aria-labelledby={id ? `${id}-title` : undefined}>
      <div className={styles.sectionHead}>
        <h2 id={id ? `${id}-title` : undefined} className={styles.sectionTitle}>
          {title}
        </h2>
        {intro && <p className={styles.sectionIntro}>{intro}</p>}
      </div>
      {children}
    </section>
  );
}

export function ButtonLink({ href, children, variant = "primary" }: { href: string; children: ReactNode; variant?: "primary" | "secondary" }) {
  return (
    <Link href={href} className={`${styles.button} ${variant === "primary" ? styles.primary : styles.secondary}`}>
      {children}
    </Link>
  );
}

export type TagTone = "live" | "gated" | "planned" | "neutral";

export function Tag({ tone = "neutral", children }: { tone?: TagTone; children: ReactNode }) {
  return <span className={`${styles.tag} ${styles[tone]}`}>{children}</span>;
}
