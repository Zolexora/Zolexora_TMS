# Tenant Control Plane

The Zolexora TMS Control Plane is hosted on Supabase (PostgreSQL). It acts as the global registry and authentication authority for the entire platform.

## Responsibilities
- Authentication and User Management (via Supabase Auth)
- Organisation Management
- RBAC and Memberships
- Infrastructure Registry (D1, MongoDB, R2)
- Tenant Database Assignments
- Platform Audit Logs
- Provisioning State Machine

## Schema Overview
- `organisations`: Core tenant business records.
- `tenant_database_registry`: Pool of available D1 databases.
- `organisation_database_assignments`: Mapping of an Organisation to a specific D1 database.
- `tenant_mongodb_registry`: Pool of available MongoDB databases.
- `organisation_mongodb_assignments`: Mapping of an Organisation to a specific MongoDB database.
- `organisation_storage_assignments`: Tenant R2 and Cloudinary prefixes.
