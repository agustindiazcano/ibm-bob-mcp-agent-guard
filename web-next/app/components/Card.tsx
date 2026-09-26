import type { ReactNode } from "react";
import styles from "./Card.module.css";

type Props = {
  title?: string;
  aside?: ReactNode;
  children: ReactNode;
};

export function Card({ title, aside, children }: Props) {
  return (
    <section className={styles.card} aria-label={title}>
      {(title || aside) && (
        <div className={styles.header}>
          {title && <h2 className={styles.title}>{title}</h2>}
          {aside}
        </div>
      )}
      {children}
    </section>
  );
}
