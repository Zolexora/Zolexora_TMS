# Tenant Data Plane

The Data Plane holds the actual business data for Zolexora TMS Organisations. It is strictly isolated per tenant using independent database instances and storage prefixes.

## Core Architecture
- **Cloudflare D1 (SQLite)**: Primary transactional database. Each tenant is assigned one logical D1 database (e.g., `zolexora-tms-dev-001`).
- **MongoDB Atlas**: Event and high-volume data plane. Each tenant gets a logical MongoDB database within the unified `Zolexora-tms` cluster.
- **Cloudflare R2**: Document object storage (RCs, Licences, PDFs). Stored in a single private bucket partitioned by tenant prefixes (`organisations/{id}/`).
- **Cloudinary**: Visual media storage (Logos, Profile photos, Vehicle photos) partitioned by tenant prefixes.

## Data Plane Routing
All API requests flow through `TenantContext`, which intercepts the JWT, resolves the user's Organisation, and looks up the assigned infrastructure resources in the Control Plane before routing the database/storage calls to the correct provider.
