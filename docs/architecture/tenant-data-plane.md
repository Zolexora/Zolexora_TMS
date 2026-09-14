# Tenant Data Plane
The data plane consists of Cloudflare D1 for transactional data, MongoDB Atlas for event and flexible data, and R2 for object storage. `TenantContext` routes requests to the correct provider.
