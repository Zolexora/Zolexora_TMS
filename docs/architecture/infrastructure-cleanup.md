# Infrastructure Cleanup & Data Reset Policy

## 1. Overview
This document defines the strict policies for wiping test/disposable Zolexora data across multiple cloud providers while guaranteeing the safety of the production environment and the core platform control plane.

## 2. Core Concepts
- **Data Reset**: This process explicitly deletes business DATA VALUES (rows, objects, documents) belonging to disposable test tenants.
- **Schema Preservation**: This process NEVER deletes database tables, Alembic migrations, or infrastructure configurations.
- **Control Plane Preservation**: The Supabase project acts as the master control plane. `organisations`, `auth.users`, and RBAC configurations are explicitly preserved so the platform can accept new tenants immediately after a reset.

## 3. Provider Policies

### Supabase / PostgreSQL
- **Target**: Tenant-specific tables (customers, vehicles, bookings, duties, financials, compliance records).
- **Execution**: `TRUNCATE public.<table_name> CASCADE`.
- **Preserved**: `auth.users`, `organisations`, registries.

### Cloudflare D1
- **Target**: Assigned pilot tenant databases.
- **Execution**: Deletion of local `pilot_*.db` mock files or issuance of Drop queries against remote pilot databases.

### MongoDB Atlas
- **Target**: Event streams (telemetry, GPS tracking).
- **Execution**: Deletion of documents within the `zolexora_{organisation_id}` logical namespace.

### Cloudflare R2
- **Target**: Compliance and invoice documents.
- **Execution**: Recursive object deletion within the `organisations/{org_id}/` logical prefix.

### Cloudinary
- **Target**: Media assets.
- **Execution**: Asset deletion within the explicitly defined test tenant folder hierarchy.

## 4. Protection & Safety
- **Production Lock**: The CLI script fails immediately if `ENVIRONMENT=production`. No override flags exist.
- **Confirmation**: Destructive execution strictly requires the `--confirm-data-reset` argument.
- **Orphan Detection**: Before cleaning storage providers, metadata is reconciled against Postgres. If discrepancies exist, they are logged as Orphans.
