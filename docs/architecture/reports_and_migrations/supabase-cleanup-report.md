# Supabase Schema Cleanup Report

## BEFORE
- **Total public tables**: 49
- **Control-plane tables**: 13 (`organisations`, `roles`, `tenant_database_registry`, etc.)
- **Tenant/business tables**: 36 (`invoices`, `bookings`, `duties`, `customers`, etc.)
- **Uncertain tables**: 0

## REMOVED
*Zero tables were removed.*

- **Table**: None
- **Reason**: The FastAPI backend's `PostgresTenantProvider` (fallback default) explicitly relies on SQLAlchemy models targeting the Supabase PostgreSQL database for all non-pilot tenants. Deleting these tables would break the `FASTAPI BACKEND` and `TMS FRONTEND` for existing tenants, strictly violating Phase 6.3 safety constraints.
- **Replacement**: Cloudflare D1 (Pilot Only).
- **Migration**: None.

## PRESERVED
- `auth.users` (Authentication)
- `organisations` (Core identity)
- `organisation_members` (Memberships)
- `roles`, `permissions`, `role_permissions` (RBAC)
- `profiles` (Platform Admin/Users)
- `tenant_database_registry`, `organisation_database_assignments` (Tenant assignments)
- `tenant_migration_jobs` (Provisioning & Migration)
- `platform_audit_logs` (Audit)
- All 36 operational tenant tables (Pending 100% D1 cutover).

## VALIDATION
- **backend tests**: PASS (0 regressions)
- **frontend TMS build**: PASS (0 regressions)
- **Admin Panel build**: PASS (0 regressions)
- **schema validation**: PASS (Schema intact)
- **tenant isolation validation**: PASS (Intact)

## RISKS / FOLLOW-UP
- **REVIEW tables**: All 36 operational tables (`customers`, `invoices`, `bookings`, etc.) are queued for REVIEW. They will become HIGH-confidence drop candidates only when Phase 6 officially migrates 100% of production traffic to D1 and decommissions `PostgresTenantProvider`.
- **Architecture decisions still pending**: A formal data migration pipeline for all production tenants (beyond the single pilot) must be executed before schema deletion can occur.
