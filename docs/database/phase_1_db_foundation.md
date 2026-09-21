# Phase 1 Database Foundation

The primary transactional source of truth is PostgreSQL/Supabase.

The first migration creates:

- `organisations`
- `profiles`
- `roles`
- `permissions`
- `role_permissions`
- `organisation_members`
- `audit_logs`

It seeds the `COMMANDER` role and the initial permission set. Organisation-owned access is controlled through membership and permission helper functions. RLS is enabled on every public table created by the migration.

## Apply locally

```bash
supabase db reset
```

Or apply the migration through the project's normal Supabase migration workflow.

## Validate with Docker Postgres

The migration was validated against PostgreSQL 16 using the repository's Docker Compose service and a minimal `auth.users`, `auth.uid()`, `authenticated`, and `anon` fixture.

The real Supabase environment supplies those Auth objects and roles.

## Tenant rule

Application code must never treat a client-supplied `organisation_id` as sufficient authorization. Server operations must use the authenticated session and permission checks; RLS remains the database enforcement layer.
