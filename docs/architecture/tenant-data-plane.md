# Tenant Data Plane Architecture

The data plane will utilize Cloudflare D1 for core transactional data.

## Responsibilities
- Customers
- Vendors
- Drivers
- Vehicles
- Bookings
- Duties
- Trips
- Rate Cards
- Financials (Invoices, Payables, Payments, Expenses)
- Compliance Engine Records

## Future State
In the future, each organisation will be assigned a dedicated (or shared) D1 database. The backend will resolve the database dynamically on every request via `TenantContext` and `TenantDatabaseProvider`.

**WARNING**: The current system continues to run entirely on PostgreSQL while we build out D1 compatibility and migration pipelines.
