---
name: tms-monorepo
description: Runbooks and architecture guidelines for the Zolexora TMS monorepo, covering Next.js 16, React 19, Tailwind v4, PostgreSQL, Docker Compose, and workspace build scripts.
---

# Zolexora TMS Monorepo Guide

This skill provides step-by-step procedures for navigating, building, running, and modifying the Zolexora TMS monorepo in Antigravity.

## Repository Architecture

The monorepo is structured as an npm workspace:
- **`apps/tms`**: Core Transportation Management System frontend (Next.js 16+, React 19, Tailwind v4). Runs on port `3000`.
- **`apps/admin`**: Administrative control dashboard (Next.js 16+, React 19, Tailwind v4). Runs on port `3001`.
- **`infrastructure/`**: Nginx proxy and deployment configuration.
- **`docker-compose.yml`**: Local and containerized development with PostgreSQL 16 (`5432:5432`).
- **`Dockerfile`**: Multi-stage production build targets (`tms` and `admin`).

## Essential Commands

Always run workspace commands from the repository root:
- **Build TMS app**: `npm run build:tms` (or `npm --prefix apps/tms run build`)
- **Build Admin app**: `npm run build:admin` (or `npm --prefix apps/admin run build`)
- **Lint TMS app**: `npm run lint:tms`
- **Lint Admin app**: `npm run lint:admin`
- **Start Database**: `docker-compose up -d postgres`

## Critical Next.js & React 19 Conventions

- Next.js 16+ has updated APIs and conventions. In monorepos, resolve packages and check `node_modules/next/dist/docs/` within each app directory.
- Maintain the Next.js generated agent headers in `apps/admin/AGENTS.md` and `apps/tms/AGENTS.md` to prevent diff churn on `next dev`.
- Tailwind CSS v4 uses `@tailwindcss/postcss` and does not rely on legacy `tailwind.config.js`.

## Verification Checklist

Before completing tasks:
1. Verify TypeScript compiles without errors in the modified app (`npm run build:tms` or `npm run build:admin`).
2. Run ESLint to ensure code cleanliness (`npm run lint:tms` or `npm run lint:admin`).
3. Ensure no secrets are committed in `.env` or configuration files.
