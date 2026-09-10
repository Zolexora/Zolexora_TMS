# 🛠️ Zolexora TMS — Complete Ecosystem CLI & Tooling Reference

This guide documents every Command-Line Interface (CLI), Model Context Protocol (MCP) server, and Agent Skill configured in the **Zolexora TMS** developer ecosystem.

---

## 📑 Table of Contents
1. [Architecture & Ecosystem Overview](#1-architecture--ecosystem-overview)
2. [GitHub CLI (`gh`)](#2-github-cli-gh)
3. [Cloudinary CLI (`cld`)](#3-cloudinary-cli-cld)
4. [Supabase CLI (`supabase`)](#4-supabase-cli-supabase)
5. [MongoDB Atlas CLI (`atlas`)](#5-mongodb-atlas-cli-atlas)
6. [Render CLI (`render`)](#6-render-cli-render)
7. [Cloudflare CLI (`wrangler`)](#7-cloudflare-cli-wrangler)
8. [Resend CLI (`resend`)](#8-resend-cli-resend)
9. [OpenAI Codex CLI (`codex`)](#9-openai-codex-cli-codex)
10. [Antigravity CLI (`agy`)](#10-antigravity-cli-agy)
11. [Model Context Protocol (MCP) Directory](#11-model-context-protocol-mcp-directory)
12. [Agent Skills Catalog & Locations](#12-agent-skills-catalog--locations)
13. [Environment Variables Reference](#13-environment-variables-reference)
14. [Quick Diagnostics Cheatsheet](#14-quick-diagnostics-cheatsheet)

---

## 1. Architecture & Ecosystem Overview

The Zolexora TMS workspace standardizes on a unified developer toolchain combining local CLI utilities, Model Context Protocol (MCP) servers for AI reasoning, and Agent Skills for domain workflows.

| Platform | Primary CLI Binary | Default Config / Auth File | Configured MCP Endpoint |
| :--- | :--- | :--- | :--- |
| **GitHub** | `gh` (v2.67.0+) | `~/.config/gh/hosts.yml` or `$GITHUB_TOKEN` | Stdio: `@modelcontextprotocol/server-github` |
| **Cloudinary** | `cld` (v1.16.1+) | `~/.config/cloudinary/` or `.env` | Stdio: `@cloudinary/asset-management` |
| **Supabase** | `supabase` (v2.117.0+) | `~/.config/supabase/access-token` | HTTP: `https://mcp.supabase.com/mcp` |
| **MongoDB Atlas** | `atlas` (v1.58.2+) | `~/.config/atlascli/config.toml` | Stdio: `mongodb-mcp-server` |
| **Render** | `render` (v2.27.0+) | `~/.render/cli.yaml` | Stdio: `render-mcp-server` (auto-token wrapper) |
| **Cloudflare** | `wrangler` (v4.130.0+) | `~/.config/.wrangler/config/default.toml` | HTTP: `https://mcp.cloudflare.com/mcp` (Code Mode) |
| **Resend** | `resend` (v2.19.1+) | `~/.config/resend/credentials.json` | HTTP: `https://mcp.resend.com/mcp` |
| **OpenAI Codex** | `codex` (v0.154.0+) | `~/.codex/config.toml` & `auth.json` | Multi-server config in `.codex/config.toml` |
| **Antigravity** | `agy` (Native) | `~/.gemini/config/mcp_config.json` | Canonical `mcp.json` in workspace root |

---

## 2. GitHub CLI (`gh`)

The GitHub CLI allows automating issues, pull requests, releases, and repository settings from the terminal.

### Key Commands
```bash
# Authentication
gh auth status                              # Verify active authentication & scopes
gh auth login                               # Interactive web/token authentication
gh auth refresh -s repo,workflow,read:org   # Add missing OAuth scopes

# Repositories
gh repo view                                # View current repo info
gh repo sync                                # Sync local branch with remote
gh repo clone <owner>/<repo>                # Clone a repository

# Pull Requests
gh pr list                                  # List open pull requests
gh pr create --title "feat: title" --body "description" # Create PR
gh pr checkout <pr-number>                  # Checkout PR branch locally
gh pr checks                                # View CI status checks for current PR
gh pr merge --auto --squash                 # Auto-merge PR when checks pass

# GitHub Actions
gh run list                                 # View recent workflow runs
gh run view <run-id> --log                  # View logs of a workflow run
gh workflow list                            # List all workflows
gh workflow run <workflow.yml>              # Trigger manual workflow run

# Codespaces & Secrets
gh codespace list                           # List active codespaces
gh secret list                              # List repository secrets
gh secret set SECRET_NAME --body "value"    # Set repo secret
```

### Global Flags
- `--repo, -R <[HOST/]OWNER/REPO>`: Target a specific repository.
- `--json <fields>`: Output structured JSON with specified fields.
- `-q, --jq <expression>`: Filter JSON output with jq expressions.
- `--help, -h`: Show command help.

---

## 3. Cloudinary CLI (`cld`)

The Cloudinary CLI (`cld`) manages media assets, uploads, transformations, and admin API resources.

### Key Commands
```bash
# Authentication & Verification
cld config                                  # Show active cloud configuration
cld login                                   # Authenticate via OAuth browser flow
cld admin ping                              # Verify connectivity (returns status: ok)

# Asset Management & Admin API
cld admin usage                             # View storage, bandwidth, and transformation quotas
cld admin resources                         # List uploaded media resources
cld admin resources -t image -m 50          # List first 50 image assets
cld admin resource <public_id>              # Fetch details for specific asset
cld admin delete_resources <public_id>      # Delete an asset

# Uploads
cld upload <file_path>                      # Upload asset to root folder
cld upload <file_path> folder="tms/assets"  # Upload asset to a designated folder
cld upload <file_path> public_id="custom_name" # Upload with explicit public_id

# URLs & Transformations
cld url <public_id>                         # Get delivery URL for asset
cld url <public_id> w=500 h=500 c=fill      # Generate transformed URL
```

### Global Flags
- `-c, --config <TEXT>`: Specify an account environment variable name.
- `-C, --config_saved <TEXT>`: Use a saved configuration profile.
- `-v, --verbosity <LVL>`: Set log level (`CRITICAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG`).

---

## 4. Supabase CLI (`supabase`)

The Supabase CLI manages local PostgreSQL containers, database migrations, remote project synchronization, and Edge Functions.

### Key Commands
```bash
# Authentication & Projects
supabase login                              # Authenticate via Personal Access Token
supabase projects list                      # List remote Supabase projects
supabase link --project-ref <ref>           # Link local directory to remote project

# Local Development (Docker-based)
supabase init                               # Initialize Supabase config in repository
supabase start                              # Start local Postgres, Studio, Auth, Storage
supabase stop                               # Stop local containers
supabase status                             # View local container URLs and service keys

# Database & Migrations
supabase db pull                            # Pull schema changes from remote DB to local migration
supabase db push                            # Apply pending local migrations to remote DB
supabase db diff -f <migration_name>        # Generate a new migration diff from schema changes
supabase db reset                           # Recreate local DB from existing migration files
supabase db lint                            # Run Postgres linter on migrations

# Secrets & Edge Functions
supabase secrets list                       # List remote environment secrets
supabase secrets set KEY=VALUE              # Set remote environment secrets
supabase functions new <function_name>      # Scaffold a new Deno Edge Function
supabase functions deploy <function_name>   # Deploy Edge Function to remote project
```

### Global Flags
- `--workdir <string>`: Path to Supabase project root.
- `--output, -o <choice>`: Output format (`env`, `pretty`, `json`, `toml`, `yaml`, `table`, `csv`).
- `--debug`: Enable verbose debug logging.
- `--yes`: Auto-confirm all prompts.

---

## 5. MongoDB Atlas CLI (`atlas`)

The Atlas CLI manages MongoDB Atlas database clusters, serverless deployments, database users, and network access lists.

### Key Commands
```bash
# Authentication & Profile
atlas auth whoami                           # Show active authenticated account & project
atlas auth login                            # Device code authorization flow
atlas config list                           # View configured profiles
atlas config set project_id <id>            # Set default Project ID

# Deployments & Clusters
atlas clusters list                         # List clusters in active project
atlas clusters describe <cluster-name>      # View cluster specs & status
atlas clusters create <name> --tier M0 --provider AWS --region US_EAST_1 # Provision cluster
atlas clusters delete <cluster-name> --force # Terminate cluster

# Database Users & Security
atlas dbusers list                          # List database authentication users
atlas dbusers create readWriteAnyDatabase --username <user> --password <pass> # Create DB user
atlas dbusers delete <username> --force     # Remove database user
atlas accessLists list                      # List IP whitelist entries
atlas accessLists create 0.0.0.0/0 --comment "Allow Everywhere" # Allow IP address

# Backups & Maintenance
atlas backups snapshots list <cluster-name> # List point-in-time snapshots
atlas metrics processes <cluster-name>      # Query hardware/throughput metrics
```

### Global Flags
- `--projectId <id>`: Target specific MongoDB Atlas project.
- `--output, -o <format>`: Format output (`json`, `plaintext`).
- `--profile, -P <name>`: Switch profile context.

---

## 6. Render CLI (`render`)

The Render CLI controls web services, background workers, Postgres databases, Key Value (Redis) datastores, and infrastructure-as-code Blueprints.

### Key Commands
```bash
# Authentication & Workspace
render whoami                               # Show active Render user identity
render login                                # Initiate browser/device OAuth login
render workspaces                           # List workspaces accessible to account
render workspace current                    # Display active workspace ID
render workspace set <workspace-id>         # Set default workspace context

# Services & Deployments
render services                             # List all services in active workspace
render services --output json               # List services in JSON format
render deploys list <service-id>            # View deployment history
render deploys create <service-id>          # Trigger new deployment
render deploys cancel <service-id> <deploy-id> # Cancel ongoing deployment
render restart <service-id>                 # Restart a service

# Logs & Sessions
render logs <service-id>                    # Tail live logs for a service
render ssh <service-id>                     # SSH directly into a service container
render psql <database-id>                   # Open interactive psql session to Render DB
render kv-cli <keyvalue-id>                 # Open interactive Valkey/Redis CLI session

# Blueprints (IaC)
render blueprints validate render.yaml      # Validate render.yaml configuration
```

### Global Flags
- `--output, -o <FORMAT>`: Output format (`interactive`, `json`, `yaml`, `text`).
- `--confirm`: Skip all confirmation prompts (ideal for scripting).

---

## 7. Cloudflare CLI (`wrangler`)

`wrangler` is the official CLI for Cloudflare Workers, Pages, D1 (SQL), KV (key-value), R2 (object storage), and Vectorize.

### Key Commands
```bash
# Authentication & Account
wrangler whoami                             # Show logged-in account and OAuth token permissions
wrangler login --device                     # Authenticate via OAuth 2.0 Device Flow
wrangler logout                             # Log out of active account

# Development & Deployments
wrangler dev                                # Start local dev server with edge emulation
wrangler deploy                             # Build and deploy Worker to Cloudflare edge
wrangler deploy --dry-run                   # Validate bundle without deploying
wrangler types                              # Generate TypeScript ambient types for bindings

# D1 Database (Serverless SQLite)
wrangler d1 list                            # List D1 databases
wrangler d1 create <db-name>                # Create a new D1 database
wrangler d1 execute <db-name> --command "SELECT * FROM users" # Run SQL query
wrangler d1 execute <db-name> --file ./schema.sql            # Run SQL migration file
wrangler d1 execute <db-name> --local --command "..."        # Query local emulated D1

# KV & R2 Storage
wrangler kv namespace list                  # List KV namespaces
wrangler kv key put --binding <KV> <key> <val> # Store key in KV
wrangler r2 bucket list                     # List R2 storage buckets
wrangler r2 object put <bucket>/<key> --file <path> # Upload file to R2

# Secrets & Environment
wrangler secret put <SECRET_NAME>           # Interactive secret creation
wrangler secret list                        # List configured secrets (names only)
wrangler tail                               # Live log streaming from deployed Workers
```

### Global Flags
- `--env, -e <env>`: Target specific environment defined in `wrangler.toml` or `wrangler.jsonc`.
- `--config, -c <path>`: Specify path to configuration file.
- `--install-skills`: Auto-install Cloudflare skills for detected AI coding agents.

---

## 8. Resend CLI (`resend`)

The official `resend-cli` manages transactional emails, verified domains, webhooks, broadcasts, and API keys.

### Key Commands
```bash
# Authentication & Diagnostics
resend whoami                               # Check authentication profile & key source
resend login --key <re_api_key>             # Save API key (non-interactive)
resend doctor                               # Run environment & credentials diagnostic audit
resend logout                               # Clear stored credentials

# Email Operations
resend emails send --to "user@example.com" \
                   --from "onboarding@resend.dev" \
                   --subject "Hello" \
                   --text "Welcome to Zolexora"  # Send plaintext email
resend emails list                          # View recent sent emails
resend emails get <email-id>                # Inspect delivery status of an email

# Domains & DNS
resend domains list                         # List configured domains
resend domains create <domain.com>          # Add a sending domain
resend domains verify <domain-id>           # Trigger DNS verification for SPF/DKIM
resend domains get <domain-id>              # View DNS records required for verification

# API Keys & Webhooks
resend api-keys list                        # List account API keys
resend api-keys create --name "CI Key"      # Generate a new API key
resend webhooks list                        # List webhook endpoints
resend logs                                 # Tail live API request logs
```

### Global Flags
- `--json`: Force structured JSON output for scripts and agents.
- `-q, --quiet`: Suppress spinners and status output (implies `--json`).
- `--api-key <key>`: Explicitly override the active API key for a single command.

---

## 9. OpenAI Codex CLI (`codex`)

`codex-cli` is OpenAI's terminal-based autonomous coding agent with full workspace sandboxing, MCP support, and Git integration.

### Key Commands
```bash
# Authentication & Diagnostics
codex login status                          # Inspect active login and authentication method
codex login --device-auth                   # Interactive ChatGPT OAuth device login
codex doctor                                # Complete system, network, sandbox & MCP diagnostic

# Interactive & Autonomous Execution
codex                                       # Start full interactive TUI coding session
codex "Fix TypeScript errors in apps/tms"   # Launch session with an initial prompt
codex exec "pnpm run lint:tms"              # Run Codex non-interactively to perform a task
codex review                                # Run autonomous code review on unstaged changes
codex apply                                 # Apply latest model diff to working tree as git patch

# MCP Server Management
codex mcp list                              # List all configured MCP servers and status
codex mcp add <name> --url <url>            # Register remote streamable HTTP server
codex mcp add <name> -- <command> [args...] # Register local stdio process server
codex mcp login <server-name>               # Authenticate OAuth-enabled MCP server
codex mcp remove <server-name>              # Remove an MCP server

# Session Management
codex resume --last                         # Resume the most recent session
codex fork --last                           # Fork current thread into a new branch
codex archive <session-id>                  # Archive a completed session
```

### Key Flags
- `-m, --model <model>`: Specify model (`o3`, `o4-mini`, `gpt-4o`).
- `-s, --sandbox <mode>`: Set sandbox policy (`read-only`, `workspace-write`, `danger-full-access`).
- `-a, --ask-for-approval <policy>`: Set human approval policy (`on-request`, `never`).
- `--dangerously-bypass-approvals-and-sandbox`: Headless execution without prompting (containers only).
- `-c, --config <key=value>`: Override TOML config values on the fly.

---

## 10. Antigravity CLI (`agy`)

The native Antigravity CLI controls agent workflows, conversation threads, MCP servers, and background execution.

### Key Commands
```bash
# Agent Sessions
agy                                         # Start interactive agent session
agy --print "Audit package.json"            # Execute prompt non-interactively and print output
agy --continue                              # Resume most recent conversation
agy --conversation <id>                     # Resume conversation by ID
agy --effort high                           # Run session with maximum reasoning effort (low|medium|high)

# MCP Management
agy mcp list                                # List all registered MCP servers and status
agy mcp add <name> <command> [args...]      # Add stdio MCP server
agy mcp add --type http <name> <url>        # Add HTTP remote MCP server
agy mcp remove <name>                       # Unregister an MCP server
```

### Global Flags
- `--dangerously-skip-permissions`: Auto-approve all tool permission requests without prompting.
- `--output-format <text|json|stream-json>`: Choose output format.
- `--sandbox`: Enforce terminal restrictions.

---

## 11. Model Context Protocol (MCP) Directory

The canonical configuration is located at [mcp.json](file:///workspaces/Zolexora_TMS/mcp.json), with symlinks at `.agents/mcp_config.json` and `.vscode/mcp.json`.

| Server Name | Transport | Endpoint / Binary | Credentials Source |
| :--- | :--- | :--- | :--- |
| **`render`** | stdio | `/usr/local/bin/render-mcp-server` | `~/.render/cli.yaml` or `$RENDER_API_KEY` |
| **`mongodb`** | stdio | `npx -y mongodb-mcp-server` | `$MONGODB_URI` |
| **`supabase`** | http | `https://mcp.supabase.com/mcp` | Remote OAuth session |
| **`cloudflare`** | http | `https://mcp.cloudflare.com/mcp` | OAuth / `$CLOUDFLARE_API_TOKEN` |
| **`cloudflare-docs`** | http | `https://docs.mcp.cloudflare.com/mcp` | Public (No auth required) |
| **`cloudflare-bindings`**| http | `https://bindings.mcp.cloudflare.com/mcp` | Remote OAuth session |
| **`cloudflare-builds`** | http | `https://builds.mcp.cloudflare.com/mcp` | Remote OAuth session |
| **`cloudflare-observability`**| http | `https://observability.mcp.cloudflare.com/mcp`| Remote OAuth session |
| **`resend`** | http | `https://mcp.resend.com/mcp` | `$RESEND_API_KEY` or `~/.config/resend/` |
| **`cloudinary`** | stdio | `npx -y @cloudinary/asset-management mcp start` | `$CLOUDINARY_*` or `.env` |
| **`github`** | stdio | `npx -y @modelcontextprotocol/server-github` | `$GITHUB_TOKEN` |
| **`ponytail`** | stdio | `node ~/.gemini/config/plugins/ponytail/ponytail-mcp/index.js` | Local filesystem |
| **`filesystem`** | stdio | `npx -y @modelcontextprotocol/server-filesystem /workspaces/Zolexora_TMS` | Local filesystem |
| **`postgres`** | stdio | `npx -y @modelcontextprotocol/server-postgres <database_url>` | Local Postgres (5432) |
| **`sequential-thinking`**| stdio | `npx -y @modelcontextprotocol/server-sequential-thinking` | Built-in |
| **`memory`** | stdio | `npx -y @modelcontextprotocol/server-memory` | Built-in |
| **`puppeteer`** | stdio | `npx -y @modelcontextprotocol/server-puppeteer` | Headless Chrome |
| **`fetch`** | stdio | `npx -y @modelcontextprotocol/server-fetch` | Built-in HTTP client |

---

## 12. Agent Skills Catalog & Locations

Skills are mirrored across three standard discovery directories:
1. Workspace: [`.agents/skills/`](file:///workspaces/Zolexora_TMS/.agents/skills)
2. Antigravity Global: `~/.gemini/config/skills/`
3. Multi-Agent Global (Codex/Claude/Amp): `~/.agents/skills/`

### Installed Skill Bundles
- **Ponytail (6 skills)**: `ponytail`, `ponytail-review`, `ponytail-audit`, `ponytail-debt`, `ponytail-gain`, `ponytail-help`
- **Cloudflare (14 skills)**: `cloudflare`, `wrangler`, `workers-best-practices`, `nextjs-on-cloudflare`, `agents-sdk`, `durable-objects`, `turnstile-spin`, `web-perf`, `cloudflare-email-service`, `cloudflare-one`, `cloudflare-one-migrations`, `sandbox-next`, `sandbox-migrate-to-next`, `sandbox-stable`
- **Render (21 skills)**: `render-cli`, `render-mcp`, `render-deploy`, `render-blueprints`, `render-web-services`, `render-private-services`, `render-background-workers`, `render-cron-jobs`, `render-static-sites`, `render-postgres`, `render-keyvalue`, `render-disks`, `render-docker`, `render-domains`, `render-env-vars`, `render-networking`, `render-scaling`, `render-debug`, `render-monitor`, `render-workflows`, `render-migrate-from-heroku`
- **Resend (5 skills)**: `resend`, `resend-cli`, `react-email`, `email-best-practices`, `agent-email-inbox`
- **MongoDB Atlas (7 skills)**: `mongodb-connection`, `mongodb-schema-design`, `mongodb-query-optimizer`, `mongodb-natural-language-querying`, `mongodb-atlas-stream-processing`, `mongodb-search-and-ai`, `mongodb-mcp-setup`
- **Supabase (2 skills)**: `supabase`, `supabase-postgres-best-practices`
- **Cloudinary (5 skills)**: `cloudinary-cli`, `cloudinary-next`, `cloudinary-react`, `cloudinary-transformations`, `cloudinary-docs`
- **Antigravity Customizations (4 skills)**: `agy-customizations`, `antigravity-guide`, `subagent-orchestration`, `generative_ui`

---

## 13. Environment Variables Reference

Values stored in [`.env`](file:///workspaces/Zolexora_TMS/.env):

```env
# Application
NODE_ENV=development
PORT=3000

# PostgreSQL (Local / Supabase)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres

# Cloudinary
CLOUDINARY_CLOUD_NAME=yfsczn8k
NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME=yfsczn8k

# Render
RENDER_API_KEY=rnd_qlPqh1tmyFH2KupYnoxP3OSBSYMO
RENDER_WORKSPACE_ID=tea-dah3ndu1egvs73cf1bng

# Cloudflare
CLOUDFLARE_ACCOUNT_ID=62f44d3cd69c56e16e40ee42a3fdc2ed

# Resend
RESEND_API_KEY=<oauth_or_api_token>

# GitHub (inherited automatically in Codespaces)
# GITHUB_TOKEN=ghu_...
```

---

## 14. Quick Diagnostics Cheatsheet

Run these one-liners anytime to verify complete ecosystem health:

```bash
# Automated Full Diagnostics across all 10 Services
pnpm cli:check
# (or: ./scripts/setup-cli-ecosystem.sh --check)

# Re-provisioning & Skill Sync
pnpm cli:setup
# (or: ./scripts/setup-cli-ecosystem.sh --all)

# 1. Antigravity & Ponytail
agy mcp list
node /home/codespace/.gemini/config/plugins/ponytail/ponytail-mcp/index.js --help 2>&1 | head -n 1

# 2. OpenAI Codex
codex doctor
codex login status
codex mcp list

# 3. GitHub
gh auth status

# 4. Cloudinary
cld admin ping

# 5. Supabase
supabase projects list

# 6. MongoDB Atlas
atlas auth whoami

# 7. Render
render whoami
render services

# 8. Cloudflare
wrangler whoami
wrangler d1 list

# 9. Resend
resend whoami
resend doctor
```
