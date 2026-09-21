# Zolexora TMS — Architecture Inspection Report

Based on an immediate audit of the existing `Zolexora_TMS` codebase, here is the state of the project mapped against the locked Q1–Q50 architectural decisions.

### 1. Existing Architecture Summary
The system is structured as a monorepo containing a unified FastAPI backend (`apps/backend`) and two React/Vite frontends: `zolexora-tms` and `zolexora-tms-admin`. Docker and Compose orchestrate local multi-container development.

### 2. Existing Frontend Structure
* **Tech Stack**: React 19, Vite, Tailwind CSS v4, Zustand, React Router, Supabase JS.
* **Layout**: Two SPAs (`zolexora-tms` and `tms-admin`). This technically conflicts with Q38 ("Avoid building separate frontend bundles for every organization unless... required"). The separation between Admin and User interfaces exists, but to support canonical platform white-labeling, we need to ensure the standard TMS app dynamically hydrates based on subdomain/configuration.

### 3. Existing Backend Structure
* **Tech Stack**: Python 3.12, FastAPI, SQLAlchemy (Async), Alembic, Uvicorn.
* **Layout**: Domain-Driven Design (DDD) with clear bounded contexts (`identity`, `core`, `operations`, `fleet`, `finance`, `crm`). 
* **State**: Module shells and routes exist, but many lack fully implemented SQLAlchemy models (e.g., Fleet, Vendors, CRM).

### 4. Existing Database/Schema
* **Models implemented**: Organisations, Users/Profiles, Roles, Permissions, RolePermissions, OrganisationMembers, plus various Platform & Customization tables.
* **Missing**: `OperatingUnit`, `Client`, `ClientLocation`, `Vendor`, and Data Scope tables.

### 5. Existing Authentication
* Supabase Auth is implemented via `@supabase/supabase-js` on the client and validated in the backend (with OTP/Resend handling in `apps/backend/app/modules/identity/auth/routes.py`).

### 6. Existing Authorization
* There is a basic `Role` & `Permission` schema, but it does NOT yet account for the layered Authorization Architecture (Q15: Organization Availability → Module Availability → Page Availability → Action Availability → Role Permissions → User Overrides → Data Scope).

### 7. Existing Tenant Model
* Implicitly bound by `Organisation` (`organisation_id`), but tenant isolation relies on manual queries rather than a central server-side scoping middleware enforcing Q32 (Tenant Isolation).

### 8. Existing Organization Model
* Currently flattened. Contains an `Organisation` table, but lacks `Operating Units` as first-class entities (Q9, Q44).

### 9. Existing Role/Permission Implementation
* A `Role` table with an `is_system` flag exists. It does not currently support `RoleVersion` (Q18) or Commander-specific role cloning constraints (Q17).

### 10. Existing Scope Implementation
* **Missing.** Data scopes (Common, Page, User overrides) (Q22-Q34) are completely unimplemented in the schema.

### 11. Existing Audit Implementation
* A `PlatformAuditLog` table exists, but it doesn't currently intercept or record organization-level configuration, impersonations, or Commander transfers (Q29).

### 12. Existing White-Label Implementation
* Customization tables exist (`OrganisationApplication`, `ApplicationConfiguration`), but the dynamic frontend runtime resolution (Q38) is missing.

### 13. Existing Domain/Subdomain Implementation
* Not yet enforced. The API runs on a static URL without dynamically resolving `X-Tenant-Domain` or evaluating subdomains to inject runtime context.

### 14. Conflicts with Locked Q1–Q50 Decisions
* **Conflict 1 (Roles):** The existing relationship mapped in `OrganisationMember` references `app.modules.roles.models.Role` instead of the newly restructured `identity` path.
* **Conflict 2 (Frontends):** We have two completely separate frontend bundles (`zolexora-tms` and `tms-admin`). We need to clarify if `tms-admin` represents the "Platform Admin" (Q5) or if both will be merged to support the "One shared configuration-driven codebase" (Q3). 
* **Conflict 3 (Entities):** The database lacks `OperatingUnit`, `Client`, and `Vendor` separation (Q9, Q10, Q14).

### 15. Recommended Implementation Sequence
1. **Fix Immediate Bugs:** Fix the SQLAlchemy relationship import error in `OrganisationMember`.
2. **Schema Alignment (Master Data):** Implement `OperatingUnit`, `Client`, `ClientLocation`, and `Vendor` tables and their respective API routes.
3. **Tenant & Auth Middleware:** Implement server-side strict tenant isolation and backend authorization resolution (Availability + Permissions + Overrides).
4. **Data Scope Engine:** Build the structured data-scope override system in the database and API.
5. **Frontend Runtime:** Update `zolexora-tms` to resolve organization context via subdomain and dynamically render the canonical sidebar based on the API's availability response.

### 16. Files/Modules That Will Need Modification
* `apps/backend/app/db/models.py`
* `apps/backend/app/modules/identity/organisations/membership_models.py`
* All frontend routing (`apps/frontend/zolexora-tms/src/routes/`)
* FastAPI dependency injections for Tenant/Auth contexts.

### 17. New Files/Modules That Are Genuinely Necessary
* `apps/backend/app/modules/identity/scopes/` (for structured data scoping)
* `apps/backend/app/modules/crm/clients/models.py`
* `apps/backend/app/modules/crm/vendors/models.py`
* `apps/backend/app/modules/operations/operating_units/models.py`

### 18. Migration Requirements
* Initial Alembic migrations must be generated for all the new structural tables (`OperatingUnit`, `Client`, `DataScope`, etc.). Existing test data in `organisations` will remain intact.

### 19. Testing Requirements
* End-to-end integration tests mimicking a standard user hitting a route with varied Data Scopes and Page Availability toggles to ensure the backend absolutely rejects unauthorized access (Q43).

### 20. Risks and Compatibility Concerns
* **Subdomain Resolution Local Testing:** Testing subdomains locally (e.g., `org1.localhost:3000`) requires specific Vite and /etc/hosts configurations.

---

### Continuation Questionnaire

**Q51. Fleet & Vehicle Ownership Model**
Does the platform support organizations owning their own vehicles natively, or are vehicles exclusively treated as vendor-supplied assets? If it supports a hybrid model, do organization-owned vehicles require the same compliance/deduction tracking as vendor vehicles?
