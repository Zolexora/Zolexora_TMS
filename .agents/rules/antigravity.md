# Antigravity Execution Standards

## Tool Execution & Safety
- Before executing modifying commands, confirm target directories and file paths.
- Avoid deleting untracked files or resetting git worktrees without explicit instructions.
- Never write credentials, private keys, or API tokens into tracked files.

## Monorepo Standards
- When modifying dependencies in `apps/tms` or `apps/admin`, ensure the workspace root `package.json` and package-locks remain in sync.
- Run `npm run lint:tms` and `npm run lint:admin` to catch ESLint warnings.
- Keep components modular and favor Tailwind CSS v4 utility classes.

## Generative UI & Visual Artifacts
- All visual widgets embedded inline must use the `<agent-embed>` syntax with a relative or `file://` URI to an artifact HTML file.
- Keep inline embeds under 500px to avoid scroll clipping.
- Use host CSS variables (`--card`, `--border`, `--foreground`, `--background`, `--primary`).
