# Zolexora TMS Dynamic Application Runtime

## Overview
Phase 6.6 establishes the **Dynamic Application Runtime**, which bridges the backend customization configuration (Phase 6.5) with the frontend React application. 
This runtime provides a secure, tenant-isolated mechanism to dynamically alter application branding, navigation, terminology, and modules without requiring code branches or separate forks for different tenants.

## Core Architectural Principle
- **Configurations remain isolated in the control-plane (Postgres).**
- **The frontend never trusts the client for determining the tenant.** Instead, it authenticates with Supabase, which determines the active organisation, which in turn securely scopes the configuration request on the backend.
- **The runtime API is normalized** into a generic format to decouple the frontend from the exact schema structure of the backend configuration tables.

## API Endpoint
`GET /api/v1/application/runtime`

This endpoint fetches:
- The base `OrganisationApplication` definition (version, status).
- The tenant's theme/branding settings.
- The enabled `ApplicationModule`s.
- `ApplicationWorkflow`, `ApplicationForm`, and `ApplicationRule` references.
- Safe defaults (e.g. if the 'bookings' module config is missing, it falls back to `enabled: True`).

**Tenant Isolation:** This endpoint implicitly depends on the `get_current_active_organisation` guard. Passing an arbitrary `organisation_id` is simply not possible; the system will only ever yield the config belonging to the authenticated organisation.

## Frontend Integration
The configuration is fetched and injected using TanStack Query via the `ApplicationRuntimeProvider` and the `useApplicationRuntime` hook.

### Navigation and Module Disabling
The `DashboardLayout` component listens to `runtime.modules` and filters its static navigation map based on whether modules like `bookings` or `duties` are enabled.

### Safe Defaults & Security
If configuration records do not exist for a tenant (e.g. they only have the `STANDARD` default record injected by onboarding), the runtime safely assumes all base modules are enabled and standard terminology applies.

Configuration merely dictates **frontend visibility**. True authorization (accessing a disabled module's API directly via cURL) remains protected by RBAC logic independently.
