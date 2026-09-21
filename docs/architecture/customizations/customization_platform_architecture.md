# Zolexora TMS Customization Platform Architecture

## Overview
Zolexora TMS has evolved from a fixed multi-tenant TMS to a Multi-Tenant Customizable TMS Platform. This architecture allows each organisation to have a substantially different application experience without forking the entire Zolexora codebase.

## Application Definitions
Configurations that define the application (Phase 6.5) belong in the Supabase control plane (Postgres), NOT the tenant's D1 transactional database. These configurations govern the application experience globally for a given tenant.

### Application Types
1. **Standard:** Out-of-the-box standard Zolexora TMS.
2. **Configured:** Standard Zolexora TMS with UI customizations, theming, and configuration toggles.
3. **Extended:** Standard Zolexora TMS with custom data modules and extended rules.
4. **Custom:** Completely custom frontend/backend applications for enterprise organisations, built on top of the Zolexora backend infrastructure.

## Control Plane Schema
The customization configurations are stored in normalized Postgres tables managed by Alembic:
- `organisation_applications`: The root definition of an organisation's application.
- `application_modules`: Granular toggles for features (e.g. `billing_enabled`).
- `application_configurations`: Global configuration options (e.g. `THEME`, `NAVIGATION`).
- `application_workflows`: Approval and state machine configurations.
- `application_rules`: Automation rules for specific entities.
- `application_forms`: Dynamic fields and UI configurations for forms.

## Design Rules
1. **No Code Hardcoding:** Never implement customer-specific logic like: `if organisation_id == "ABC": do_special_thing()`. Use the configuration tables instead.
2. **Tenant Isolation:** All APIs under `/api/v1/application` strict check the `user.organisation_id` to ensure tenants cannot read or modify other tenants' configurations.
3. **Provisioning Hooks:** When a new organisation is created, the system provisions a default `STANDARD` `OrganisationApplication` for them.
