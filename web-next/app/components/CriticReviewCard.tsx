"use client";

import React from "react";
import styles from "./CriticReviewCard.module.css";

interface Props {
  note: string;
}

// Renders inline formatted text (`code`, **bold**, etc.)
function renderInlineFormatted(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  // Tokenize `code`, **bold**, and plain text
  const regex = /(`[^`]+`)|(\*\*[^*]+\*\*)|(\*[^*]+\*)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }

    const [token, code, bold, italic] = match;
    if (code) {
      parts.push(
        <code key={key++} className={styles.codePill}>
          {code.slice(1, -1)}
        </code>
      );
    } else if (bold) {
      parts.push(
        <strong key={key++} className={styles.boldText}>
          {bold.slice(2, -2)}
        </strong>
      );
    } else if (italic) {
      parts.push(<em key={key++}>{italic.slice(1, -1)}</em>);
    } else {
      parts.push(token);
    }

    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : [text];
}

interface ParsedReview {
  targetFile: string;
  verdict: "APPROVED" | "REJECTED" | "REVIEW";
  intro: string[];
  sections: { title: string; items: string[] }[];
}

function parseCriticNote(rawNote: string): ParsedReview {
  let targetFile = "Test Suite Verification";
  let content = rawNote.trim();

  // Check if note starts with a file path like "shop/inventory.py: ..."
  const filePrefixMatch = content.match(/^([a-zA-Z0-9_\-./]+\.py):\s*([\s\S]*)$/);
  if (filePrefixMatch) {
    targetFile = filePrefixMatch[1];
    content = filePrefixMatch[2].trim();
  }

  // Detect verdict
  let verdict: "APPROVED" | "REJECTED" | "REVIEW" = "REVIEW";
  if (/verdict:\s*\**approved\**/i.test(content) || /\bapproved\b/i.test(content)) {
    verdict = "APPROVED";
  } else if (/verdict:\s*\**rejected\**/i.test(content) || /\brejected\b/i.test(content)) {
    verdict = "REJECTED";
  }

  const lines = content.split("\n");
  const intro: string[] = [];
  const sections: { title: string; items: string[] }[] = [];
  let currentSection: { title: string; items: string[] } | null = null;

  for (let line of lines) {
    line = line.trim();
    if (!line) continue;

    // Check for verdict line itself (to avoid repeating in body)
    if (/^\**verdict\**:\s*\**[a-zA-Z]+\**/i.test(line)) {
      continue;
    }

    // Check for markdown headers
    const headerMatch = line.match(/^#{2,4}\s+(.*)$/);
    if (headerMatch) {
      if (currentSection) {
        sections.push(currentSection);
      }
      currentSection = {
        title: headerMatch[1],
        items: [],
      };
      continue;
    }

    // If inside a section
    if (currentSection) {
      currentSection.items.push(line);
    } else {
      // Intro lines before first heading
      intro.push(line);
    }
  }

  if (currentSection) {
    sections.push(currentSection);
  }

  return { targetFile, verdict, intro, sections };
}

export function CriticReviewCard({ note }: Props) {
  const review = parseCriticNote(note);

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div className={styles.targetFile}>
          <span>Target Module: {review.targetFile}</span>
        </div>
        <div>
          {review.verdict === "APPROVED" && (
            <span className={styles.badgeApproved}>
              <span>✓</span> APPROVED
            </span>
          )}
          {review.verdict === "REJECTED" && (
            <span className={styles.badgeRejected}>
              <span>✕</span> REJECTED
            </span>
          )}
          {review.verdict === "REVIEW" && (
            <span className={styles.badgeReview}>
              ADVISORY
            </span>
          )}
        </div>
      </div>

      <div className={styles.body}>
        {review.intro.length > 0 && (
          <div className={styles.intro}>
            {review.intro.map((p, i) => (
              <p key={i} style={{ marginBottom: "6px" }}>
                {renderInlineFormatted(p)}
              </p>
            ))}
          </div>
        )}

        {review.sections.map((section, idx) => (
          <div key={idx} className={styles.section}>
            <div className={styles.sectionTitle}>
              <span>{section.title}</span>
            </div>
            <ul className={styles.list}>
              {section.items.map((item, itemIdx) => {
                // Check if item is a bullet or number
                const bulletMatch = item.match(/^[-*]\s+(.*)$/);
                const numberMatch = item.match(/^(\d+\.)\s+(.*)$/);
                let contentText = item;
                let marker = "•";

                if (bulletMatch) {
                  contentText = bulletMatch[1];
                  marker = "•";
                } else if (numberMatch) {
                  marker = numberMatch[1];
                  contentText = numberMatch[2];
                }

                // Check if item starts with **Key**:
                const keyMatch = contentText.match(/^(\*\*[^*]+:\*\*|\*\*[^*]+\*\*:\s*)(.*)$/);
                if (keyMatch) {
                  const keyText = keyMatch[1].replace(/\*/g, "");
                  const restText = keyMatch[2];
                  return (
                    <li key={itemIdx} className={styles.listItem}>
                      <span className={styles.itemMarker}>{marker}</span>
                      <div className={styles.itemContent}>
                        <span className={styles.itemKey}>{keyText}</span>
                        {renderInlineFormatted(restText)}
                      </div>
                    </li>
                  );
                }

                return (
                  <li key={itemIdx} className={styles.listItem}>
                    <span className={styles.itemMarker}>{marker}</span>
                    <div className={styles.itemContent}>
                      {renderInlineFormatted(contentText)}
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}

        {review.verdict === "APPROVED" && (
          <div className={styles.verdictBannerApproved}>
            <div className={styles.verdictText}>
              <span>CRITIC VERDICT: APPROVED</span>
            </div>
            <span className={styles.verdictSub}>
              Assertion rigor, state isolation & boundary safety verified
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
