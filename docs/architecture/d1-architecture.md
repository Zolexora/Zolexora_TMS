# D1 Architecture and Compatibility Report

## Current Stack
- PostgreSQL 16
- SQLAlchemy (asyncpg)
- Alembic

## D1 (SQLite) Limitations vs PostgreSQL

### 1. Data Types
- **UUIDs**: D1 supports standard text for UUIDs. PostgreSQL has native UUID types. We must handle type coercion.
- **JSONB**: D1 supports JSON text functions, but not native binary JSONB. We lose advanced indexing (GIN).
- **ENUMs**: D1 uses CHECK constraints or text instead of native ENUM types.
- **DateTime**: D1 expects text (ISO-8601) or unix epoch integers. PostgreSQL uses native TIMESTAMP WITH TIME ZONE.

### 2. Constraints & Indexing
- Foreign key constraints require PRAGMA foreign_keys = ON; support is sometimes different in SQLite.
- Partial indexes syntax differs.

### 3. SQLAlchemy & Alembic
- Async operations in D1 via python require `aiohttp` or Cloudflare Workers APIs. We cannot simply use `asyncpg`. We will likely need to write an SQLAlchemy dialect or execute raw REST API queries.

### 4. Transactions
- D1 supports transactions, but locking behavior in SQLite under high concurrency is different from PostgreSQL MVCC.

## Mitigation Strategy
We must test D1 compatibility by creating a dry-run migration of one tenant before attempting production cutover. The backend currently uses an abstracted `TenantDatabaseProvider` which defaults to `PostgresTenantProvider`.
