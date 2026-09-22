# Zolexora TMS

## Getting Started

```bash
git clone https://github.com/Zolexora/Zolexora_TMS
pnpm install
```

> `pnpm install` automatically installs the pre-commit hook via the `prepare` script.

---

## Environment Variables

This repo uses [dotenvx](https://dotenvx.com) to safely commit an **encrypted** `.env` to version control.

### How it works
- `.env` — encrypted, committed to the repo (safe to share)
- `.env.keys` — your private decryption key, **never committed** (gitignored)

### Adding a new key
1. Add it in plain text to `.env`:
   ```bash
   echo "NEW_KEY=value" >> .env
   ```
2. Re-encrypt:
   ```bash
   echo "" | pnpm dotenvx encrypt
   ```
3. Commit:
   ```bash
   git add -f .env && git commit -m "chore: add NEW_KEY"
   ```

### Pre-commit hook
A pre-commit hook in [`scripts/hooks/pre-commit`](scripts/hooks/pre-commit) automatically encrypts `.env` before every commit — so you can't accidentally commit plaintext secrets.

It is installed automatically by `pnpm install` via the `prepare` script in [`package.json`](package.json).

### Running with decrypted env
```bash
pnpm dotenvx run -- <your-command>
```
