# Supabase Drop Candidates

> **CRITICAL ARCHITECTURAL FINDING**
> 
> Under the current architecture, Phase 6.1 explicitly dictates that D1 acts as a **CONTROLLED PILOT ONLY**. The `TenantDatabaseProvider` abstraction allows routing a single pilot tenant to D1, while the fallback `PostgresTenantProvider` actively serves all other production tenants directly from Supabase PostgreSQL.
>
> Dropping tenant data tables from Supabase would instantly break the FastAPI backend, Alembic migrations, and SQLAlchemy models for the entire non-pilot platform. Thus, there are ZERO high-confidence drop candidates at this exact stage of the migration.

### Table: ALL TENANT TABLES (e.g. `customers`, `bookings`, `invoices`)
- **WHY OBSOLETE**: Not obsolete. They are required by `PostgresTenantProvider`.
- **OLD ARCHITECTURE PURPOSE**: Primary storage of all operational tenant data.
- **CURRENT REPLACEMENT**: Partially replaced by Cloudflare D1 for the *Pilot Tenant only*.
- **CODE REFERENCES**: `app/modules/*/routes.py`, `app/modules/*/models.py`, `app/modules/*/schemas.py`, `app/modules/*/service.py`.
- **DATABASE REFERENCES**: Intensive foreign key web across all modules.
- **FRONTEND REFERENCES**: Indirectly via API schemas.
- **MIGRATION REFERENCES**: Fully managed by existing Alembic migration history.
- **RLS REFERENCES**: Relies on `organisation_id` checks.
- **TRIGGER REFERENCES**: Audit triggers and timestamp updates.
- **SAFE TO DROP**: **NO**
- **CONFIDENCE**: **LOW**
- **NOTES**: Cannot be dropped until 100% of production tenants are successfully migrated to D1 and the `PostgresTenantProvider` is formally decommissioned.

### Conclusion
There are **0** HIGH confidence drop candidates. All tenant tables are marked **REVIEW** pending the completion of the D1 cutover.
