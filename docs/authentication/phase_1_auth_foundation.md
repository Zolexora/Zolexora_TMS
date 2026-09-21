# Phase 1 Authentication Foundation

## Boundaries

The customer TMS uses Supabase Auth. The platform admin application remains a separate application and must use a separate platform-admin authorization boundary.

The `service_role` key is server-only. Browser code uses only `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`.

## Flow

1. The onboarding form calls `auth.signUp` with email/password and Google OAuth uses the `/auth/callback` route.
2. Supabase sends the verification email when email confirmation is enabled.
3. The callback exchanges the authorization code for a session.
4. If onboarding metadata is present, `complete_onboarding` creates the organisation, Commander membership, and audit record in one database transaction.
5. Dashboard requests are refreshed and protected by the customer app proxy.

The metadata is used only as input to the self-service onboarding transaction. It is not used for authorization. Authorization comes from `organisation_members`, `roles`, `permissions`, and PostgreSQL RLS.

## Required Supabase configuration

- Configure Google OAuth in Supabase Auth.
- Add the customer callback URL to the Supabase Auth redirect allow list.
- Enable email confirmation.
- Apply `supabase/migrations/202609100001_phase1_foundation.sql`.
- Set the public Supabase URL and publishable/anon key in the customer app environment.

## Current limitation

The UI and database transaction are ready, but no remote Supabase project is configured in this workspace. Until those environment variables and Auth settings are supplied, clicking an auth action will return a configuration error instead of contacting a project.
