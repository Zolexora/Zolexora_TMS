# MongoDB Event/Telemetry Plane

MongoDB Atlas is used for flexible, high-volume event data that doesn't fit well in relational schema or requires heavy geographic/time-series queries.

## Data Stored
- GPS Pings
- Vehicle Telemetry
- Mobile App Event Logs
- Dispatch Webhook Payloads

## Tenant Isolation
Instead of one cluster per tenant, we use a Shared Cluster model where tenant separation is enforced via specific databases (`tms_events_{org_id}`) or specific prefixed collections within a shared database (`org_{id}_gps`).
