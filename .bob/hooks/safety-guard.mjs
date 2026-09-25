/**
 * safety-guard.mjs — PreToolUse fail-closed hook for TestMind AI
 *
 * Blocks outright (exit 2, no confirmation prompt) any tool call that would:
 *   1. Delete or empty PENDING.md
 *   2. Edit demo-repo/shop/ or demo-repo/web/ from repoguard-fixer or repoguard-test-writer modes
 *   3. Delete or rename anything under .bob/
 *
 * "Edit is fine; delete or empty is not" — file edits to PENDING.md pass through.
 *
 * Registered as a PreToolUse hook in .bob/settings.json.
 */

import { readFileSync } from "node:fs";

let raw = "";
for await (const chunk of process.stdin) raw += chunk;

let input;
try {
  input = JSON.parse(raw);
} catch {
  // Malformed input — fail open so Bob is not broken by a parse error
  process.exit(0);
}

const tool = input.tool_name ?? "";
const ti   = input.tool_input ?? {};

// ── helpers ──────────────────────────────────────────────────────────────────

function block(reason) {
  process.stderr.write(`[safety-guard] BLOCKED: ${reason}\n`);
  process.exitCode = 2;
}

/** Normalise a path string: forward slashes, no leading ./ */
function norm(p) {
  return String(p ?? "").replace(/\\/g, "/").replace(/^\.\//, "");
}

/** True when the normalised path matches or is under the given prefix */
function under(path, prefix) {
  const p = norm(path);
  return p === prefix || p.startsWith(prefix + "/");
}

// ── 1. PENDING.md — block delete / empty, allow edits ────────────────────────

// execute_command: rm PENDING.md, git rm PENDING.md, git clean, shell redirection > PENDING.md
if (tool === "execute_command") {
  const cmd = String(ti.command ?? "");

  // rm / git rm
  if (/\brm\b.*PENDING\.md/.test(cmd) || /\bgit\s+rm\b.*PENDING\.md/.test(cmd)) {
    block("Deleting PENDING.md is not allowed. Edit its content instead.");
  }

  // shell truncation:  > PENDING.md  or  : > PENDING.md  or  echo "" > PENDING.md  etc.
  if (/>\s*PENDING\.md/.test(cmd) && !/>>/.test(cmd.replace(/.*>>\s*PENDING/, ""))) {
    // allow >>  (append); block >  (truncate/overwrite to empty)
    // More precise: block if there's a bare > to PENDING.md
    if (/(?<![>])\s*>\s*PENDING\.md/.test(cmd)) {
      block("Redirecting to PENDING.md (which would empty it) is not allowed.");
    }
  }

  // git clean -f / -fd / -fdx that would remove PENDING.md
  if (/\bgit\s+clean\b/.test(cmd)) {
    block("git clean may delete PENDING.md. Run git clean manually after confirming safe paths.");
  }
}

// write_file targeting PENDING.md with empty content
if (tool === "write_file" && norm(ti.path) === "PENDING.md") {
  const content = String(ti.content ?? "");
  if (content.trim() === "") {
    block("Writing empty content to PENDING.md is not allowed.");
  }
}

// ── 2. demo-repo/shop/ and demo-repo/web/ — block from fixer/test-writer modes ──

// We detect the active mode from the session_id prefix (Bob encodes mode in session ids
// when launched via custom modes) OR from a REPOGUARD_MODE env hint.
// Because mode info is not directly in the PreToolUse payload, we read .bob/current-mode
// if it exists (written by the SessionStart hook if wired), and fall back to env.
let activeMode = "";
try {
  activeMode = readFileSync(".bob/current-mode", "utf8").trim().toLowerCase();
} catch {
  activeMode = (process.env.REPOGUARD_MODE ?? "").toLowerCase();
}

const restrictedModes = ["repoguard-fixer", "repoguard-test-writer", "fixer", "test-writer"];
const isRestrictedMode = restrictedModes.some(m => activeMode.includes(m));

if (isRestrictedMode) {
  const editTools = ["write_file", "apply_diff", "search_and_replace", "insert_content"];
  if (editTools.includes(tool)) {
    const targetPath = norm(ti.path ?? "");
    if (under(targetPath, "demo-repo/shop") || under(targetPath, "demo-repo/web")) {
      block(
        `Mode '${activeMode}' may only edit files under tests/. ` +
        `Editing ${targetPath} would change the demo-repo source and invalidate all documented numbers. ` +
        `If this is intentional, switch to the Orchestrator mode and make an explicit decision.`
      );
    }
  }
  if (tool === "execute_command") {
    const cmd = String(ti.command ?? "");
    // Block writes to demo-repo/shop or demo-repo/web via shell redirection
    if (/demo-repo\/(shop|web)/.test(cmd) && /\s*>/.test(cmd)) {
      block(
        `Mode '${activeMode}' may not write to demo-repo/shop/ or demo-repo/web/ via shell commands.`
      );
    }
  }
}

// ── 3. .bob/ — block delete or rename ────────────────────────────────────────

if (tool === "execute_command") {
  const cmd = String(ti.command ?? "");

  // rm -rf .bob/  or  rm .bob/custom_modes.yaml  etc.
  if (/\brm\b.*\.bob\//.test(cmd)) {
    block(
      "Deleting files under .bob/ is not allowed without user confirmation. " +
      "The Bob modes, rules, and skills are the product's agent configuration."
    );
  }

  // git mv / mv renaming .bob files
  if (/\b(git\s+mv|mv)\b.*\.bob\//.test(cmd)) {
    block(
      "Renaming files under .bob/ is not allowed without user confirmation."
    );
  }

  // git clean inside .bob
  if (/\bgit\s+clean\b.*\.bob/.test(cmd)) {
    block("git clean targeting .bob/ is not allowed without user confirmation.");
  }
}

// write_file / apply_diff / search_and_replace targeting .bob files is ALLOWED
// (agents need to update rules and skills) — only delete/rename is blocked above.
