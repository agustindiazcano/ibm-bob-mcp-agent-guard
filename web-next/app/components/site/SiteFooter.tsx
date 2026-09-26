import Link from "next/link";
import { BobBadge, Brand } from "./Brand";
import { ABOUT_LINKS, PRODUCT_LINKS, REPO_URL, repoDoc, type SiteLink } from "./links";
import styles from "./SiteFooter.module.css";

const SOURCE_LINKS: SiteLink[] = [
  { href: REPO_URL, label: "GitHub repository" },
  { href: repoDoc("docs/ARCHITECTURE.md"), label: "Architecture" },
  { href: repoDoc("docs/DATA_PLATFORM.md"), label: "Data platform plan" },
  { href: repoDoc("PENDING.md"), label: "Roadmap" },
];

function Column({ title, links, external }: { title: string; links: SiteLink[]; external?: boolean }) {
  return (
    <div className={styles.column}>
      <h2 className={styles.heading}>{title}</h2>
      <ul className={styles.list}>
        {links.map(({ href, label }) => (
          <li key={href}>
            {external ? (
              <a href={href} target="_blank" rel="noreferrer" className={styles.link}>
                {label}
              </a>
            ) : (
              <Link href={href} className={styles.link}>
                {label}
              </Link>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function SiteFooter() {
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.top}>
          <div className={styles.about}>
            <Brand />
            <p className={styles.tagline}>
              Measures whether a Python repo&rsquo;s tests actually catch bugs, then has AI agents write the missing
              ones. Every number comes from the engine, never from a model.
            </p>
          </div>
          <Column title="Product" links={PRODUCT_LINKS} />
          <Column title="About" links={ABOUT_LINKS} />
          <Column title="Source" links={SOURCE_LINKS} external />
        </div>
        <div className={styles.bottom}>
          <span>
            Built by{" "}
            <a href="https://orcid.org/0009-0001-4336-490X" target="_blank" rel="noreferrer" className={styles.link}>
              Agustin Diaz-Cano
            </a>{" "}
            &middot; Team Argentina
          </span>
          <span className={styles.edition}>
            <BobBadge size="sm" />
            <span>edition</span>
          </span>
        </div>
      </div>
    </footer>
  );
}
