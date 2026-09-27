"use client";

import { useMemo, useState } from "react";
import type { FixFile } from "../lib/types";
import styles from "./CodeViewer.module.css";

interface Props {
  files: FixFile[];
  initialActiveIndex?: number;
}

// Tokenizes a single line of Python code into styled spans
function highlightPythonLine(line: string): React.ReactNode[] {
  if (!line) return [" "];

  // Regex rules
  const commentMatch = line.match(/^(\s*)(#.*)$/);
  if (commentMatch) {
    return [
      commentMatch[1],
      <span key="c" className={styles.tokComment}>{commentMatch[2]}</span>,
    ];
  }

  // Tokenization patterns
  const tokens: React.ReactNode[] = [];
  let remaining = line;
  let keyIndex = 0;

  // Single regex with capturing groups for tokenizer
  const tokenRegex =
    /(@[\w\.]+)|(f?"""[\s\S]*?"""|f?'''[\s\S]*?'''|f?"(?:\\.|[^"\\])*"|f?'(?:\\.|[^'\\])*')|(#.*$)|(\bdef\s+[a-zA-Z_]\w*)|(\bclass\s+[a-zA-Z_]\w*)|(\b(?:def|class|return|import|from|as|assert|raise|try|except|finally|with|if|elif|else|for|while|break|continue|pass|lambda|yield|async|await|in|is|not|and|or)\b)|(\b(?:True|False|None)\b)|(\b(?:self|cls|int|str|float|bool|list|dict|set|tuple|len|range|print|pytest)\b)|(\b\d+(?:\.\d+)?\b)/g;

  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = tokenRegex.exec(line)) !== null) {
    if (match.index > lastIndex) {
      tokens.push(remaining.substring(lastIndex, match.index));
    }

    const [
      full,
      decorator,
      str,
      comment,
      defName,
      clsName,
      keyword,
      constant,
      builtin,
      num,
    ] = match;

    if (decorator) {
      tokens.push(<span key={keyIndex++} className={styles.tokDecorator}>{decorator}</span>);
    } else if (str) {
      tokens.push(<span key={keyIndex++} className={styles.tokString}>{str}</span>);
    } else if (comment) {
      tokens.push(<span key={keyIndex++} className={styles.tokComment}>{comment}</span>);
    } else if (defName) {
      const parts = defName.split(/\s+/);
      tokens.push(
        <span key={keyIndex++}>
          <span className={styles.tokKeyword}>{parts[0]} </span>
          <span className={styles.tokDef}>{parts[1]}</span>
        </span>
      );
    } else if (clsName) {
      const parts = clsName.split(/\s+/);
      tokens.push(
        <span key={keyIndex++}>
          <span className={styles.tokKeyword}>{parts[0]} </span>
          <span className={styles.tokDef}>{parts[1]}</span>
        </span>
      );
    } else if (keyword) {
      tokens.push(<span key={keyIndex++} className={styles.tokKeyword}>{keyword}</span>);
    } else if (constant) {
      tokens.push(<span key={keyIndex++} className={styles.tokConstant}>{constant}</span>);
    } else if (builtin) {
      tokens.push(<span key={keyIndex++} className={styles.tokBuiltin}>{builtin}</span>);
    } else if (num) {
      tokens.push(<span key={keyIndex++} className={styles.tokNumber}>{num}</span>);
    } else {
      tokens.push(full);
    }

    lastIndex = tokenRegex.lastIndex;
  }

  if (lastIndex < line.length) {
    tokens.push(line.substring(lastIndex));
  }

  return tokens.length > 0 ? tokens : [line];
}

export function CodeViewer({ files, initialActiveIndex = 0 }: Props) {
  const [activeIndex, setActiveIndex] = useState(
    Math.min(initialActiveIndex, Math.max(0, files.length - 1))
  );
  const [copied, setCopied] = useState(false);

  const activeFile = files[activeIndex] || files[0];

  const lines = useMemo(() => {
    if (!activeFile?.content) return [];
    return activeFile.content.split("\n");
  }, [activeFile?.content]);

  const handleCopy = async () => {
    if (!activeFile?.content) return;
    try {
      await navigator.clipboard.writeText(activeFile.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore clipboard error
    }
  };

  if (!files || files.length === 0) {
    return null;
  }

  return (
    <div className={styles.container}>
      <div className={styles.topBar}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div className={styles.windowControls} aria-hidden="true">
            <span className={`${styles.dot} ${styles.dotRed}`} />
            <span className={`${styles.dot} ${styles.dotYellow}`} />
            <span className={`${styles.dot} ${styles.dotGreen}`} />
          </div>

          <div className={styles.fileTabs}>
            {files.map((file, idx) => {
              const fileName = file.path.split("/").pop() || file.path;
              const isActive = idx === activeIndex;
              return (
                <button
                  key={file.path}
                  type="button"
                  className={`${styles.tab} ${isActive ? styles.tabActive : ""}`}
                  onClick={() => setActiveIndex(idx)}
                >
                  <span className={styles.fileIcon}>🐍</span>
                  <span>{fileName}</span>
                  <span
                    className={`${styles.statusPill} ${
                      file.status === "added" ? styles.statusAdded : styles.statusModified
                    }`}
                  >
                    {file.status === "added" ? "+new" : "~mod"}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        <div className={styles.actions}>
          <span className={styles.metaInfo}>
            {lines.length} lines · {activeFile?.path}
          </span>
          <button
            type="button"
            className={`${styles.copyButton} ${copied ? styles.copied : ""}`}
            onClick={handleCopy}
            title="Copy test code"
          >
            {copied ? (
              <>
                <span>✓</span>
                <span>Copied!</span>
              </>
            ) : (
              <>
                <span>📋</span>
                <span>Copy Code</span>
              </>
            )}
          </button>
        </div>
      </div>

      <div className={styles.codeArea}>
        <table className={styles.codeTable}>
          <tbody>
            {lines.map((line, i) => (
              <tr key={i} className={styles.lineRow}>
                <td className={styles.lineNum}>{i + 1}</td>
                <td className={styles.lineContent}>
                  {highlightPythonLine(line)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
