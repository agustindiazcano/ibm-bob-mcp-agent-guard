"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { BobBadge, Brand } from "./Brand";
import { DemoSwitch } from "./DemoSwitch";
import { ABOUT_LINKS, DEMO_SLIDES, PRODUCT_LINKS, REPO_URL, type SiteLink } from "./links";
import { useDemoMode } from "../../context/DemoModeContext";
import styles from "./SiteNav.module.css";

const ALL_NAV_LINKS: SiteLink[] = [...PRODUCT_LINKS, ...ABOUT_LINKS];

function isActive(pathname: string, href: string): boolean {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}

function NavLinks({ links, pathname, onNavigate }: { links: SiteLink[]; pathname: string; onNavigate?: () => void }) {
  return links.map(({ href, label }) => {
    const active = isActive(pathname, href);
    return (
      <Link
        key={href}
        href={href}
        className={`${styles.link} ${active ? styles.active : ""}`}
        aria-current={active ? "page" : undefined}
        onClick={(e) => {
          (e.currentTarget as HTMLElement).blur();
          onNavigate?.();
        }}
      >
        {label}
      </Link>
    );
  });
}

export function SiteNav() {
  const pathname = usePathname();
  const router = useRouter();
  const { demoMode } = useDemoMode();
  const [open, setOpen] = useState(false);
  const close = () => setOpen(false);

  // Active navigation items depending on whether Demo Mode is enabled
  const navItems = demoMode ? DEMO_SLIDES : ALL_NAV_LINKS;

  // Keyboard navigation: ArrowLeft and ArrowRight to navigate across navbar tabs or slides
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      // Don't trigger if user is typing in form controls
      const activeEl = document.activeElement;
      const tag = activeEl?.tagName?.toLowerCase();
      if (
        tag === "input" ||
        tag === "textarea" ||
        tag === "select" ||
        (activeEl as HTMLElement)?.isContentEditable
      ) {
        return;
      }

      if (e.key === "ArrowRight") {
        const idx = navItems.findIndex((link) => isActive(pathname, link.href));
        if (idx >= 0 && idx < navItems.length - 1) {
          e.preventDefault();
          (document.activeElement as HTMLElement)?.blur();
          router.push(navItems[idx + 1].href);
        } else if (idx === -1) {
          e.preventDefault();
          (document.activeElement as HTMLElement)?.blur();
          router.push(navItems[0].href);
        }
      } else if (e.key === "ArrowLeft") {
        const idx = navItems.findIndex((link) => isActive(pathname, link.href));
        if (idx > 0) {
          e.preventDefault();
          (document.activeElement as HTMLElement)?.blur();
          router.push(navItems[idx - 1].href);
        }
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [pathname, router, navItems]);

  return (
    <header className={styles.bar}>
      <nav className={styles.inner} aria-label="Main">
        <Brand />

        {demoMode ? (
          <div className={styles.slideLinks} role="tablist" aria-label="Demo Slides">
            {DEMO_SLIDES.map((slide) => {
              const active = isActive(pathname, slide.href);
              const numStr = String(slide.slideNumber).padStart(2, "0");
              return (
                <Link
                  key={slide.href}
                  href={slide.href}
                  className={`${styles.slideLink} ${active ? styles.slideLinkActive : ""}`}
                  aria-current={active ? "page" : undefined}
                  title={`Slide ${numStr}: ${slide.slideTitle}`}
                  onClick={(e) => {
                    (e.currentTarget as HTMLElement).blur();
                    close();
                  }}
                >
                  <span>{numStr}</span>
                </Link>
              );
            })}
          </div>
        ) : (
          <div className={styles.links}>
            <NavLinks links={PRODUCT_LINKS} pathname={pathname} />
            <span className={styles.divider} aria-hidden="true" />
            <NavLinks links={ABOUT_LINKS} pathname={pathname} />
          </div>
        )}

        <div className={styles.end}>
          <DemoSwitch />
          <BobBadge />
          <a className={styles.iconLink} href={REPO_URL} target="_blank" rel="noreferrer" aria-label="Source on GitHub">
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M8 0a8 8 0 0 0-2.53 15.59c.4.07.55-.17.55-.38v-1.33c-2.23.48-2.7-1.07-2.7-1.07-.36-.92-.89-1.17-.89-1.17-.73-.5.05-.49.05-.49.8.06 1.23.83 1.23.83.72 1.22 1.88.87 2.34.66.07-.52.28-.87.5-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.6 7.6 0 0 1 4 0c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48v2.2c0 .21.15.46.55.38A8 8 0 0 0 8 0Z" />
            </svg>
          </a>
          <button
            type="button"
            className={styles.menuButton}
            aria-expanded={open}
            aria-controls="site-menu"
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((v) => !v)}
          >
            <svg viewBox="0 0 20 20" aria-hidden="true">
              {open ? <path d="M5 5l10 10M15 5L5 15" /> : <path d="M3 6h14M3 10h14M3 14h14" />}
            </svg>
          </button>
        </div>
      </nav>

      {open && (
        <div id="site-menu" className={styles.menu}>
          {demoMode ? (
            <>
              <span className={styles.menuLabel}>Demo Slides ({DEMO_SLIDES.length})</span>
              {DEMO_SLIDES.map((slide) => {
                const active = isActive(pathname, slide.href);
                return (
                  <Link
                    key={slide.href}
                    href={slide.href}
                    className={`${styles.link} ${active ? styles.active : ""}`}
                    onClick={close}
                  >
                    <span style={{ fontWeight: 700, marginRight: 8, color: "var(--accent)" }}>
                      {String(slide.slideNumber).padStart(2, "0")}
                    </span>
                    {slide.slideTitle}
                  </Link>
                );
              })}
            </>
          ) : (
            <>
              <span className={styles.menuLabel}>Product</span>
              <NavLinks links={PRODUCT_LINKS} pathname={pathname} onNavigate={close} />
              <span className={styles.menuLabel}>About</span>
              <NavLinks links={ABOUT_LINKS} pathname={pathname} onNavigate={close} />
            </>
          )}
        </div>
      )}
    </header>
  );
}
