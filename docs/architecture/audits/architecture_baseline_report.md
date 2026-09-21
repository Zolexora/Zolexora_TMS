# Zolexora TMS — Architecture Baseline Report

This report presents a thorough inspection of the existing Zolexora TMS development project. No code modifications, migrations, or architectural changes have been executed during this task. This serves strictly as the baseline for future implementation phases.

---

## A. Current Project Summary
The current Zolexora TMS is a multi-tenant monorepo SaaS application running a FastAPI (Python 3.12) backend and two React/Vite frontends (`zolexora-tms` and `tms-admin`). It uses a centralized PostgreSQL database managed by Alembic, with Supabase handling identity (JWT). The backend is structured using Domain-Driven Design (DDD) principles (contexts like `identity`, `core`, `operations`, `fleet`, `finance`). However, the implementation is currently incomplete. It lacks mature domain models for essential transportation entities (Clients, Vendors, Data Scopes), lacks sophisticated white-label dynamic routing, and relies on basic Role-Based Access Control (RBAC) rather than the layered availability/scope authorization architecture required.

## B. Current Architecture
* **Frontend**: React 19, Vite, Tailwind CSS v4, Zustand, Tanstack Query, React Router.
* **Backend**: Python 3.12, FastAPI, SQLAlchemy (Async), Uvicorn.
* **Database**: PostgreSQL 16 (Relational/Master data), Redis (OTP/Caching). (Note: `TenantContext` references MongoDB, but primary infrastructure is Postgres).
* **Authentication**: Supabase Auth (JWT handling on client, validated via `verify_supabase_jwt` in FastAPI).
* **Authorization**: Standard RBAC (`OrganisationMember` → `Role` → `Permission`).
* **Infrastructure**: Local Docker Compose (Postgres, Redis), Render planned for production, Supabase self-hosted/external setup.

## C. Existing Domain Model
* **Implemented Entities**: `Organisation`, `User`, `Role`, `Permission`, `OrganisationMember`, `OperatingUnit`, `OperatingUnitLocation` (recently scaffolded), and configuration metadata tables (`OrganisationApplication`, etc.).
* **Missing Entities**: `Client`, `ClientLocation`, `Vendor`, `DataScope` models, and detailed Fleet/Operations schemas.

## D. Existing Authorization Model
* **Identity**: Supabase JWT (`sub`) mapped to the Postgres `profiles` table.
* **Tenant**: Handled via `organisation_id` lookup in the `organisation_members` join table upon authentication. Stored in `TenantContext`.
* **Role/Permission**: The `Role` entity is fetched during auth to populate the user's `role_code` and a string array of `permissions`. Hardcoded `COMMANDER` bypass exists in the backend `has_permission()` method.
* **Scope**: Unimplemented. No structured data scope engine exists.
* **Availability**: Partially unimplemented. The frontend fetches `/api/v1/application/runtime`, but backend authorization guards (`require_permission`) do not currently evaluate module/page availability states.

## E. Existing White-Label Model
* Database tables (`ApplicationConfiguration`, `ApplicationModule`) exist to store configuration.
* The frontend uses an `ApplicationRuntimeProvider` to fetch runtime configuration.
* **Conflict**: Dynamic subdomain resolution is not natively implemented in the routing layout. The presence of two distinct frontends (`zolexora-tms`, `tms-admin`) technically violates the true single-frontend-white-label architecture unless `tms-admin` is strictly reserved for *Zolexora Platform Admins* (not Commanders).

## F. Existing Domain Model Conflicts
* **Client & Client Location**: Missing entirely. Must be implemented strictly as separate entities from Operating Units.
* **Vendor**: Missing entirely. Must not be conflated with Clients.
* **Platform Admin vs Commander**: Currently, `PLATFORM_ADMIN` is checked as a standard permission string within a user's permission array. This is a severe risk if a Commander modifies roles and accidentally assigns a platform-level permission.
* **Frontend Apps**: The dual-frontend setup (`zolexora-tms` vs `tms-admin`) risks creating parallel logic.

## G. Q1–Q50 Gap Matrix

| Area | Existing | Required | Status | Action |
| :--- | :--- | :--- | :--- | :--- |
| **Q1-Q3 Architecture** | Monorepo, split UI | Single Shared Platform UI | Partially Implemented | Consolidate Commander/User workflows into canonical runtime; isolate Platform Admin. |
| **Q4, Q7-Q8 White-label** | `ApplicationConfiguration` | Config-driven UI/Subdomain | Partially Implemented | Implement subdomain parsing middleware in API and Frontend. |
| **Q5-Q6 Application Model** | Static React Routes | Dynamic Availability Render | Conflicting | Bind React Router to API availability tree. |
| **Q9, Q44-Q45 Operating Units**| `OperatingUnit` & `Location` | First-class entities | Already Correct | Recently scaffolded; needs API routes. |
| **Q10 Subdomain Onboarding** | None | Real-time subdomain check | Missing | Implement `/api/v1/platform/check-subdomain`. |
| **Q11-Q12, Q35 Commander** | Role string `"COMMANDER"` | Unrestricted (minus disabled) | Conflicting | Prevent `"COMMANDER"` from bypassing *Availability* checks. |
| **Q13, Q15-Q20 Roles** | Basic RBAC | Versioning, Immutable Templates| Missing | Add `RoleVersion` table; lock system templates. |
| **Q21-Q26 Availability** | Not enforced on API | Explicit API & UI blocks | Missing | Inject Availability check before `require_permission`. |
| **Q27-Q34 Data Scope** | None | Hierarchical, Role/User/Page | Missing | Build structural Scope schema and SQLAlchemy filters. |
| **Q36-Q38 Impersonation** | None | Audited actor/subject context | Missing | Implement Impersonation JWT generation and UI indicator. |
| **Q39-Q42 Cmdr Transfer** | None | Strict transfer workflow | Missing | Implement Transfer Commander API with strong audit. |
| **Q46-Q50 Clients/Vendors** | None | Separate from OUs, Transfers | Missing | Create `Client`, `ClientLocation`, `Vendor` and transfer logs. |

## H. Database Gap Analysis (Future Schema Changes)
1.  **CRM Models**: Create `clients`, `client_locations`, `vendors` tables.
2.  **Relationship History**: Create `client_location_operating_unit_history` to track transfers (Previous OU, New OU, Actor, Timestamp) without destroying historical records.
3.  **Scope Engine**: Create `role_scopes`, `user_scope_overrides`, and `page_scope_overrides` tables mapping to canonical entity types (OU, Client, etc.).
4.  **Audit**: Create `impersonation_logs` and `commander_transfer_logs`.
5.  **Role Versioning**: Alter `roles` to include `version` and `is_immutable_template`.

## I. Frontend Gap Analysis
1.  **Subdomain Resolution**: Update `zolexora-tms` initialization to parse `window.location.hostname` and fetch runtime config specifically for that subdomain.
2.  **Navigation Tree**: Refactor the hardcoded `DashboardLayout` sidebar to dynamically render only enabled and permitted pages based on the combined Authorization + Availability payload.
3.  **Impersonation UI**: Develop a global, always-visible banner indicating impersonation state.

## J. Backend Gap Analysis
1.  **Tenant Middleware**: Implement an `X-Tenant-Domain` header or subdomain parser to establish the `TenantContext` *before* authenticating the user, ensuring the user belongs to the requested domain.
2.  **Authorization Pipeline**: Refactor `require_permission` in `dependencies.py` to become `require_access(page, action)` which evaluates: `Availability -> Permission -> Scope`.
3.  **Impersonation Handling**: Create an API endpoint for Commander to request an impersonated JWT containing both `actor_id` (Commander) and `sub` (Target User).

## K. Security Gap Analysis
*   **Tenant Isolation Risks**: Currently, developers must manually remember to filter by `organisation_id` in every repository query. A structural SQLAlchemy interceptor (or Postgres RLS) is highly recommended to prevent accidental cross-tenant data leaks.
*   **Authorization Risks**: Disabled capabilities (Availability) are not checked by the backend. A user could theoretically use Postman to hit a disabled module's API if their role retains the permission.
*   **Platform Admin Leakage**: Platform Admin is checked via a normal string in the permission array (`PLATFORM_ADMIN`). This should be separated into a distinct `PlatformUser` table to ensure Commanders cannot grant themselves platform access.

## L. Migration Risks
*   **Role Migration**: Transitioning the flat `permissions` array into `RoleVersion` constructs will require a careful data backfill to preserve existing tenant configurations.
*   **Location Data**: If any legacy logic assumed `Organisation` was the sole operational location, existing organizational metadata must be migrated into the new `OperatingUnit` hierarchy.

## M. Recommended Implementation Sequence
To adhere to the principle of vertical slicing without disrupting the existing platform, the following sequence is recommended for subsequent prompts:

1.  **Phase 1: Domain Entities (Master Data)**
    *   Implement `Client`, `ClientLocation`, `Vendor`, and `ClientLocationOUHistory` models, migrations, and basic CRUD APIs.
2.  **Phase 2: Platform Architecture Validation (Subdomains & Isolation)**
    *   Implement `X-Tenant-Domain` middleware.
    *   Implement systemic SQLAlchemy Tenant Isolation (preventing manual query mistakes).
3.  **Phase 3: The Authorization & Availability Pipeline**
    *   Refactor backend dependencies to evaluate Availability + Permissions.
    *   Implement Role Versioning and Immutable Templates logic.
4.  **Phase 4: The Data Scope Engine**
    *   Implement structural Data Scope tables and the SQLAlchemy query modifiers to enforce them.
5.  **Phase 5: Commander Capabilities**
    *   Implement Impersonation (JWT + UI indicator).
    *   Implement Commander Transfer workflow with associated Audit Logs.
6.  **Phase 6: Frontend Canonical Render**
    *   Bind the React Router and Navigation sidebar to the newly unified Authorization/Availability/Scope API payload.
