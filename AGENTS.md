# Antigravity Workspace Guidelines

This document defines the core operational standards, tooling workflows, and architectural guidelines for AI agents working within the **Zolexora TMS** workspace.

---

## 1. Antigravity Agent Operations & Workflow

- **Reactive Wakeup & Zero Polling**: Antigravity resumes agent execution reactively when background tasks or subagents finish. Never run loops or poll status commands. Once background execution is triggered, yield execution by stopping tool calls.
- **Scheduling over Sleep**: Never invoke `sleep` in terminal commands. Use the native `schedule` tool for delayed wakeups or recurring cron executions.
- **Subagent Utilization**:
  - Use `research` subagents for extensive file audits, repository reconnaissance, or searching documentation without cluttering primary context.
  - Use `self` subagents for isolated task execution requiring workspace tools.
  - Define specialized subagents via `define_subagent` when repetitive domain-specific roles are needed.
- **Clickable File Links**: Always link to referenced files using clickable GitHub-style markdown links with the `file://` scheme and file basenames (e.g., [package.json](file:///workspaces/Zolexora_TMS/package.json) or [docker-compose.yml](file:///workspaces/Zolexora_TMS/docker-compose.yml)).

---

## 2. Generative UI & Visual Artifacts

When generating interactive components, previews, or data visualizations:
- **Tailwind CDN**: Use the approved gstatic Tailwind script:
  `<script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>`
- **Theme Variables**: Use semantic design tokens (`bg-[var(--card)]`, `text-[var(--foreground)]`, `border-[var(--border)]`, `bg-[var(--background)]`). Do not define local color fallbacks on `:root`.
- **Inline Widgets (`<agent-embed>`)**:
  - Keep widgets compact (under 500px in height).
  - Set `<body class="bg-transparent ...">` so the widget blends into the chat container.
  - Wrap content in card containers with borders and padding.
- **Standalone Artifacts**: For complex dashboards or workflows, save standalone `.html` artifacts to be viewed in the side auxiliary pane.

---

## 3. Model Context Protocol (MCP) Integration

MCP servers are configured in `.agents/mcp_config.json` and globally in `~/.gemini/config/mcp_config.json`:
- **`filesystem`**: Scoped file operations across the repository.
- **`fetch`**: Fetch external web documentation and API endpoints.
- **`sequential-thinking`**: Deep reasoning and step-by-step problem breakdown.
- **`memory`**: Persistent cross-session knowledge and entity tracking.
- **`puppeteer`**: Automated headless browser testing and UI inspection.
- **`postgres`**: Database queries against local PostgreSQL (`5432:5432`).
- **`github`**: GitHub repository management, issues, and PR interactions.

Manage servers via the Antigravity CLI:
```bash
agy mcp list
agy mcp add <name> <commandOrUrl> [args...]
```

---

## 4. Zolexora TMS Monorepo Architecture

- **Structure**:
  - `apps/tms`: TMS Client Application (Next.js 16+, React 19, Tailwind CSS v4, port 3000).
  - `apps/admin`: TMS Admin Dashboard (Next.js 16+, React 19, Tailwind CSS v4, port 3001).
  - `infrastructure/`: Reverse proxy and deployment configurations.
  - `docker-compose.yml`: Multi-container setup with PostgreSQL 16.
- **Development Scripts**:
  - `npm run build:tms`: Compile TMS frontend.
  - `npm run build:admin`: Compile Admin frontend.
  - `npm run lint:tms` / `npm run lint:admin`: Run ESLint across apps.
- **Next.js Conventions**: Next.js 16+ has breaking architectural changes. Consult `node_modules/next/dist/docs/` for internal API references. Retain Next.js agent blocks in `apps/*/AGENTS.md`.
- **Code Cleanliness**: Preserve all existing comments and docstrings. Verify TypeScript builds before completing tasks.

---

## 5. Ponytail: Lazy Senior Dev Decision Ladder

Enforce minimalism, avoid over-engineering, and write the minimum code that works. Before writing any code, climb this ladder:

1. **Does this need to be built at all?** (YAGNI - You Aren't Gonna Need It).
2. **Does it already exist in this codebase?** Reuse existing helpers, utilities, or patterns; do not duplicate logic.
3. **Does the standard library already do this?** Use built-in JavaScript/Node/TypeScript standard methods.
4. **Does a native platform feature cover it?** Use native Web API or runtime features.
5. **Does an already-installed dependency solve it?** Leverage existing packages rather than adding new ones.
6. **Can this be one line?** Prefer simple, readable one-liners or concise logic over heavy abstractions.
7. **Only then**: Write the minimum code that works.

**Core Directives**:
- No abstractions that weren't explicitly requested.
- No new dependencies if existing ones or stdlib suffice.
- Deletion over addition. Boring over clever. Fewest files possible.
- Shortest working diff wins once the root cause and problem flow are fully understood.

