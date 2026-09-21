# Tenant Migration Architecture

## Pilot Procedure
This document describes the Phase 6.1 pilot migration pipeline to transition individual organisations from PostgreSQL to Cloudflare D1.
The entire pipeline runs without modifying the authoritative production Postgres cluster.

## Architecture
- **TenantMigrationService**: Orchestrates the state machine and coordinates sub-components.
- **TenantDataExporter**: Reads data directly from PostgreSQL for a single tenant, respecting tenant boundaries.
- **TenantDataTransformer**: Handles type-mapping to make PG data D1-compatible (see rules below).
- **TenantDataImporter**: Provisions the D1 schema and safely imports rows.
- **TenantDataReconciler**: Ensures that exported row counts match imported counts and critical financial totals align EXACTLY.
- **TenantRuntimeValidator**: Executes mock operations (reads, eventually writes) against the `D1TenantProvider` to ensure code compatibility.

## Type Mappings (PostgreSQL -> D1/SQLite)
- `UUID` -> `TEXT`
- `ENUM` -> `TEXT` (Application must enforce domain)
- `JSONB` -> `TEXT` (Canonical deterministic JSON serialization)
- `BOOLEAN` -> `INTEGER` (0 / 1)
- `TIMESTAMP WITH TIME ZONE` -> `TEXT` (ISO-8601 UTC representation)
- `DECIMAL / NUMERIC` -> `TEXT` (String representations preserve exact precision to prevent drift).

## Reconciliation Methodology
1. Raw counts for every migrated table are compared between PG and D1.
2. The `invoices` table undergoes a strict summation of `grand_total` (calculating in python from exact string representations) to ensure no financial drift occurred.

## Rollback Procedure
Because the PostgreSQL authoritative tables are untouched, a rollback consists entirely of destroying the pilot D1 database and marking the `TenantMigrationJob` as `MIGRATION_CANCELLED`. The user's `TenantContext` will automatically fall back or remain pointed to PostgreSQL.

## Status: PILOT_VALIDATION_COMPLETE
All isolated offline testing passes safely. The next stage is a read-write shadow mode over live HTTP requests.
