---
name: bitwarden
description: >
  Use when working with Bitwarden CLI (`bw`) for secret management — storing,
  retrieving, and rotating secrets in the Bitwarden vault. Covers login/unlock
  flows, creating and fetching secure notes and passwords, integrating with
  dotenvx for encrypted .env key storage, and wiring the Bitwarden MCP server.
  Trigger: "bitwarden", "bw vault", "store secret in bitwarden", "get secret
  from bitwarden", "DOTENV_PRIVATE_KEY bitwarden", "rotate secret", "bw login",
  "bw unlock", "bw get", "bw create".
---

# Bitwarden Skill

Use this skill when the user wants to store, retrieve, or manage secrets using
the Bitwarden CLI (`bw`) or the Bitwarden MCP server.

---

## CLI Basics

```bash
# Login (interactive)
bw login

# Unlock vault and export session token
export BW_SESSION=$(bw unlock --raw)

# Check login status
bw login --check

# Sync vault (pull latest from server)
bw sync --session "$BW_SESSION"
```

---

## Store a Secret (Secure Note)

```bash
# Create a secure note with a value
bw get template item | \
  jq --arg name "Zolexora TMS DOTENV_PRIVATE_KEY" \
     --arg value "YOUR_KEY_VALUE" \
  '.name = $name | .type = 2 | .secureNote.type = 0 | .notes = $value' | \
  bw encode | bw create item --session "$BW_SESSION"
```

---

## Retrieve a Secret

```bash
# Get a password item by name
bw get password "Zolexora TMS DOTENV_PRIVATE_KEY" --session "$BW_SESSION"

# Get notes from a secure note item
bw get item "Zolexora TMS DOTENV_PRIVATE_KEY" --session "$BW_SESSION" | jq -r '.notes'
```

---

## Integration with dotenvx

Store the `DOTENV_PRIVATE_KEY` in Bitwarden so no `.env.keys` file is needed on disk:

```bash
# One-liner: unlock vault and export key for dotenvx
export BW_SESSION=$(bw unlock --raw)
export DOTENV_PRIVATE_KEY=$(bw get password "Zolexora TMS DOTENV_PRIVATE_KEY" --session "$BW_SESSION")

# Then run any command with decrypted env
pnpm dotenvx run -- npm start
```

### Pre-commit hook with Bitwarden

The hook at `scripts/hooks/pre-commit` can be extended to pull the key from Bitwarden:

```bash
#!/bin/sh
if git diff --cached --name-only | grep -q "^\.env$"; then
  echo "🔐 Fetching DOTENV_PRIVATE_KEY from Bitwarden..."
  export BW_SESSION=$(bw unlock --raw)
  export DOTENV_PRIVATE_KEY=$(bw get password "Zolexora TMS DOTENV_PRIVATE_KEY" --session "$BW_SESSION")
  echo "" | pnpm dotenvx encrypt
  git add -f .env
fi
```

---

## Bitwarden MCP Server

The Bitwarden MCP server (`bitwarden-mcp`) allows AI agents to read/write vault
items directly. It is configured in `mcp.json` and requires `BW_SESSION` to be
set in the environment.

```json
"bitwarden": {
  "command": "npx",
  "args": ["-y", "@bitwarden/mcp"],
  "env": {
    "BW_SESSION": "${BW_SESSION}"
  }
}
```

### Start MCP server manually

```bash
export BW_SESSION=$(bw unlock --raw)
npx -y @bitwarden/mcp
```

---

## Security Notes

- Never commit `BW_SESSION` — it expires after vault lock/logout.
- Use `bw lock` to revoke the session when done.
- Prefer secure notes over password items for storing raw key material.
- The `DOTENV_PRIVATE_KEY` in `.env.keys` can be deleted once stored in Bitwarden.
