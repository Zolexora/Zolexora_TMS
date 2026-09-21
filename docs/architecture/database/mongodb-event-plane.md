# MongoDB Event Plane

MongoDB Atlas is used exclusively for event streams, high-volume telemetry, and flexible external integration payloads. It is NOT the primary transactional database.

## Hierarchy Rules
Zolexora TMS Organisation ≠ MongoDB Atlas Organization.

Our strict hierarchy is:
MongoDB Atlas
└── Atlas Organization
    └── Zolexora TMS Project
        └── Cluster: Zolexora-tms
            ├── zolexora_tenant_001
            ├── zolexora_tenant_002
            └── ... (up to 010)

## Use Cases
- `gps_events`: Raw coordinate streams.
- `telemetry`: Vehicle OBD/IoT data.
- `dispatch_events`: State changes in duty lifecycles.
- `webhook_events`: Payloads from external systems.

We use ONE cluster (`Zolexora-tms`) with multiple logical databases for tenant isolation.
