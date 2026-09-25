# IBM Bob — Skills, Hooks, Safety Guard & Agent Context

Quick reference for Bob's key features and configuration.

---

## 🧠 Memory & LLM Statelessness

Bob (like all LLMs) is **stateless** — each new conversation starts with zero memory of previous ones.
There is **no `memory.md`** file. The persistence mechanism is `AGENTS.md`.

| Mechanism | Purpose |
|---|---|
| `AGENTS.md` | Persistent project context loaded every conversation |
| `/init` command | Auto-generates `AGENTS.md` by scanning your codebase |
| `/memory refresh` | (Bob Shell) Reloads all `AGENTS.md` files |
| `/memory show` | (Bob Shell) Displays the current loaded context |

---

## 📁 Project Context — `AGENTS.md`

Bob uses **`AGENTS.md`** (not `memory.md`, not `CLAUDE.md`). Loaded hierarchically:

1. **Global** — `~/.bob/AGENTS.md` (all projects)
2. **Project root** — `AGENTS.md` (and parent directories)
3. **Subdirectory** — `AGENTS.md` in component folders (component-specific instructions)

### Run `/init` to generate everything

```
your-project/
├── AGENTS.md                           ← main project context
└── .bob/
    ├── rules-code/AGENTS-code.md       ← Agent mode context
    ├── rules-plan/AGENTS-plan.md       ← Plan mode context
    ├── rules-ask/AGENTS-ask.md         ← Ask mode context
    └── rules-advanced/AGENTS-advanced.md
```

Typical `AGENTS.md` contents:
- Project overview and purpose
- Directory structure and key file locations
- Technology stack and dependencies
- Architectural patterns and conventions
- Development workflows

> Re-run `/init` after major project changes to keep context current.

---

## 🎯 Skills

Skills are **reusable instruction sets** (recipes) for specialized workflows. Bob reads the `description`
to decide when to activate a skill, then loads the full instructions via `use_skill` — **once per conversation**.

### File structure

```
your-project/
└── .bob/
    └── skills/
        └── code-review/
            ├── SKILL.md              ← required
            ├── checklist.md          ← optional supporting files
            ├── severity-guide.md
            └── scripts/
                └── analyze.sh
```

Global skills: `~/.bob/skills/`

### `SKILL.md` format

```markdown
---
name: code-review
description: Review code for bugs, security issues, and best practices
---

When reviewing code, check for:
- Security vulnerabilities
- Performance issues
- Missing error handling at API boundaries
- Unused imports and dead code

Provide a summary with severity levels for each finding.
```

**Required frontmatter fields:**
- `name` — display name used in the Bob interface
- `description` — helps Bob decide when to activate; skills without a description are ignored

**Supporting files** alongside `SKILL.md` can include checklists, templates, reference docs, scripts, and style guides. Bob can read them automatically once the skill is activated.

### Approval & auto-approve

By default Bob asks permission before activating a skill. To skip the prompt:
**Settings → Auto-Approve → Skills → toggle on**

Loaded skills consume the **Skills** token budget in the context window.

### Best practices

- Start simple; refine based on results
- Keep `SKILL.md` concise — move detailed content to companion files
- Use single-responsibility skills (one focused task, not a catch-all)
- Include project skills in version control for team consistency

---

## 🪝 Hooks

Hooks let you **run shell commands or POST to HTTPS endpoints** automatically on Bob lifecycle events.

**Scopes:**
- Workspace: `.bob/settings.json`
- Global: `~/.bob/settings/settings.json`

Both scopes are combined — a workspace hook does not replace a matching global hook.

### 7 supported events

| Event | When it runs | Matcher | Can block? | Typical use |
|---|---|---|---|---|
| `SessionStart` | Task starts, resumes, or finishes compaction | `startup`, `resume`, `compact` | No | Load dynamic project context |
| `UserPromptSubmit` | Before a prompt is processed | *(omit)* | **Yes** (exit 2) | Reject a prompt that violates policy |
| `PreCompact` | Before manual or automatic compaction | `manual`, `auto` | **Yes** (exit 2) | Block compaction or inspect custom instructions |
| `PostCompact` | After compaction succeeds | `manual`, `auto` | No | Record the generated summary |
| `PreToolUse` | Before tool approval and execution | Bob tool name | **Yes** (exit 2 or structured JSON) | Block a tool call that violates a policy |
| `PostToolUse` | After a tool succeeds | Bob tool name | No (already ran) | Run linter/formatter, report findings |
| `Stop` | After the root task loop stops | *(omit)* | No | Record completion or perform cleanup |

Matchers are **JavaScript regular expressions**. Examples:
- `^startup$` — new sessions only
- `^execute_command$` — only the execute_command tool
- `^(write_file|apply_diff|search_and_replace|insert_content)$` — all write tools
- `^mcp__github__` — all tools from the GitHub MCP server

### Example hook configuration

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "^execute_command$",
        "hooks": [
          {
            "type": "command",
            "command": "node .bob/hooks/guard-publish.mjs",
            "timeout": 10
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "^(write_file|apply_diff|search_and_replace|insert_content)$",
        "hooks": [
          {
            "type": "command",
            "command": "node .bob/hooks/lint-write.mjs",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

### Input payload (sent to every handler)

Bob sends one JSON object via stdin (command) or POST body (HTTP):

```json
{
  "session_id": "task-123",
  "cwd": "/workspace/project",
  "hook_event_name": "PreToolUse",
  "tool_name": "execute_command",
  "tool_input": { "command": "pnpm publish" },
  "tool_use_id": "tool-456"
}
```

Additional fields per event:
- `SessionStart` → `source` (`startup`, `resume`, `compact`)
- `UserPromptSubmit` → `prompt`
- `PreCompact` / `PostCompact` → `trigger`, `custom_instructions` / `compact_summary`
- `PostToolUse` → all PreToolUse fields + `tool_response`
- `Stop` → `last_assistant_message`

### Blocking a tool call (PreToolUse)

**Exit 2** (simple):
```js
// .bob/hooks/guard-publish.mjs
let raw = "";
for await (const chunk of process.stdin) raw += chunk;
const input = JSON.parse(raw);

if (input.tool_name === "execute_command" &&
    input.tool_input?.command?.includes("publish")) {
  process.stderr.write("Publishing requires review — use the release workflow.");
  process.exitCode = 2;
}
```

**Structured JSON** (can also rewrite the tool input):
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Publishing requires review"
  }
}
```

### HTTP handler

```json
{
  "type": "http",
  "url": "https://audit.example.com/hooks",
  "headers": { "Authorization": "Bearer ${AUDIT_TOKEN}" },
  "allowedEnvVars": ["AUDIT_TOKEN"],
  "timeout": 10
}
```

> Hooks run only in **trusted workspaces**. Handler errors fail open. Only exit 2 from `PreToolUse` or `UserPromptSubmit` blocks the action.

---

## 🛡️ Safety Guard

### This project: `ibm-bob-mcp-agent-guard`

This workspace is an **MCP server** that acts as a policy enforcement layer at the tool-call level.
It connects to Bob via MCP and intercepts/guards tool usage programmatically.

### Built-in Bob safety layers

| Layer | Description |
|---|---|
| Tool approval prompts | Shown before every tool call (read, write, execute, MCP) |
| Auto-approve controls | Configurable per tool group, per task, or globally |
| MCP tool allow/deny | `includeTools` / `excludeTools` per server in settings |
| MCP server allow/deny list | `mcp.allowed` / `mcp.excluded` arrays in settings |
| Trusted folders | Untrusted workspaces disable all auto-approve and hooks |
| Sandbox mode | Wraps `execute_command` in Docker / Podman / macOS sandbox |
| `PreToolUse` hooks | Programmatic guard — intercept and block before execution |

### MCP tool filtering (settings.json)

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node dist/server.js",
      "includeTools": ["safe_tool_a", "safe_tool_b"],
      "excludeTools": ["dangerous_tool"]
    }
  }
}
```

---

## 🧩 Agent Context Window

The context window is **200,000 tokens** (270k cap total). Categories:

| Category | What it holds | When it grows |
|---|---|---|
| **System prompt** | Bob's core instructions | Flat — set at task start |
| **Tool definitions** | Built-in tool schemas | Flat — set at task start |
| **MCP Tools** | Connected MCP server tool schemas | When you add MCP servers/tools |
| **Rules** | `AGENTS.md` files (project + mode) | Set when task opens |
| **Skills** | Loaded skill instructions | When a skill is activated mid-thread |
| **Messages** | Prompts, replies, file reads, tool output | Every turn — grows the most |

### Context tips

- Use `/init` to populate `AGENTS.md` once, not re-read files every session
- Disable unused MCP tools to save token budget
- Start a new task (`+`) to get a fresh window — files on disk are not affected
- Use subagents for repo-wide reads so only results (not every tool step) land in Messages
- Keep `AGENTS.md` and Rules short and operational

---

## 📂 `.bob/` Folder Reference

```
.bob/
├── settings.json              ← workspace settings (hooks, MCP, tools, approval)
├── AGENTS.md                  ← (if manually placed here)
├── rules-code/AGENTS-code.md  ← Agent mode context (generated by /init)
├── rules-plan/AGENTS-plan.md  ← Plan mode context
├── rules-ask/AGENTS-ask.md    ← Ask mode context
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md           ← required: name + description frontmatter
│       └── ...                ← optional supporting files
└── hooks/
    └── <hook-script>.mjs      ← hook command scripts
```

Global equivalents all live under `~/.bob/`.
