# Tenant Control Plane Architecture

The Supabase database serves as the platform control plane.

## Responsibilities
- User Authentication (Supabase Auth)
- Organisation Registry
- Organisation Membership & Platform RBAC
- Tenant Database Assignments (D1 registry)
- Tenant MongoDB Assignments
- Tenant Storage Prefixes (Cloudinary / R2)
- Provisioning State Machine tracking
- Platform Audit Logging

## Separation of Concerns
The control plane DOES NOT store operational TMS data (Bookings, Duties, Invoices, Customers).
It acts exclusively as a router and metadata registry for authenticating a user, discovering their organisation, and returning the `TenantContext` to tell the backend where to perform the requested operation.
