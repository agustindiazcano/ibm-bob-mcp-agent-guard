/**
 * evidence-export.mjs — Stop hook for TestMind AI
 *
 * When a repoguard-mode task finishes, automatically exports the task session
 * report to bob-evidence/, named NN-short-description.md (auto-incrementing).
 *
 * The last assistant message is used as the report body; the filename slug is
 * derived from the first meaningful heading or sentence in that message.
 *
 * Registered as a Stop hook in .bob/settings.json.
 */

import { readdirSync, writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

let raw = "";
for await (const chunk of process.stdin) raw += chunk;

let input;
try {
  input = JSON.parse(raw);
} catch {
  process.exit(0);
}

// Only export for repoguard modes
let activeMode = "";
try {
  const { readFileSync } = await import("node:fs");
  activeMode = readFileSync(".bob/current-mode", "utf8").trim().toLowerCase();
} catch {
  activeMode = (process.env.REPOGUARD_MODE ?? "").toLowerCase();
}

const repoguardModes = [
  "orchestrator", "analyzer", "fixer", "gate", "visual-agent", "reporter",
  "repoguard"
];
const isRepoguardMode = repoguardModes.some(m => activeMode.includes(m));

if (!isRepoguardMode) {
  process.exit(0);
}

const lastMessage = String(input.last_assistant_message ?? "").trim();
if (!lastMessage) {
  process.exit(0);
}

// ── Determine next sequential number ─────────────────────────────────────────

const evidenceDir = join(input.cwd ?? ".", "bob-evidence");
try {
  mkdirSync(evidenceDir, { recursive: true });
} catch { /* already exists */ }

let maxN = 0;
try {
  for (const f of readdirSync(evidenceDir)) {
    const m = f.match(/^(\d+)-/);
    if (m) maxN = Math.max(maxN, parseInt(m[1], 10));
  }
} catch { /* empty dir is fine */ }

const nextN = String(maxN + 1).padStart(2, "0");

// ── Derive a slug from the last message ──────────────────────────────────────

function toSlug(text) {
  // Try first markdown heading
  const headingMatch = text.match(/^#+\s+(.+)/m);
  const source = headingMatch ? headingMatch[1] : text.split(/[.\n]/)[0];
  return source
    .toLowerCase()
    .replace(/[^a-z0-9 ]/g, "")
    .trim()
    .replace(/\s+/g, "-")
    .slice(0, 50)
    .replace(/-+$/, "");
}

const slug = toSlug(lastMessage) || "session";
const filename = `${nextN}-${slug}.md`;
const filepath = join(evidenceDir, filename);

// ── Write the evidence file ───────────────────────────────────────────────────

const timestamp = new Date().toISOString();
const modeLabel = activeMode || "unknown";

const content = `# Bob Evidence — ${filename}

**Mode:** ${modeLabel}  
**Exported:** ${timestamp}  
**Session:** ${input.session_id ?? "unknown"}

---

${lastMessage}
`;

try {
  writeFileSync(filepath, content, "utf8");
  // Print to stdout so Bob adds it as context (optional, kept brief)
  process.stdout.write(`[evidence-export] Saved ${filename}\n`);
} catch (err) {
  // Fail open — evidence export must never break a session
  process.stderr.write(`[evidence-export] Could not write ${filepath}: ${err.message}\n`);
}
