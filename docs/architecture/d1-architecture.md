# Cloudflare D1 Architecture

Cloudflare D1 is the primary transactional database for Zolexora TMS. It replaces the legacy multi-tenant PostgreSQL schema.

## Provisioning Strategy
We maintain a pre-provisioned pool of 10 D1 databases:
- `zolexora-tms-dev-001`
- `zolexora-tms-dev-002`
- ...
- `zolexora-tms-dev-010`

These are tracked in the `tenant_database_registry` table in the Control Plane.

## Schema Deployment
D1 uses a SQLite-compatible dialect. The base schema (`d1_tenant_schema.sql`) includes:
- customers
- vendors
- drivers
- vehicles
- rate_cards
- bookings
- duties
- invoices
- payments

## Isolation Guarantees
Cross-tenant data leakage is physically impossible at the database layer because each Organisation receives a dedicated SQLite database file distributed via Cloudflare's edge network.
