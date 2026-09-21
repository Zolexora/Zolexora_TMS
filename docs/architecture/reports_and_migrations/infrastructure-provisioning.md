# Infrastructure Provisioning & State Machine

## CLI Tooling
Infrastructure is managed safely via the backend CLI:
`python -m app.cli.infrastructure <command>`

Commands:
- `audit` / `verify`: Verifies actual resources against the Control Plane registry.
- `plan`: Shows required changes.
- `provision`: Requires `--confirm-infrastructure-provision`. Safely creates missing registries.
- `orphans`: Detects resource drift between Cloudflare/Mongo/R2 and Supabase.

## State Machine
Tenant assignments follow a strict lifecycle:
`REQUESTED` -> `PROVISIONING` -> `RESOURCE_CREATED` -> `SCHEMA_INITIALIZING` -> `READY`

Failure paths result in `PROVISIONING_FAILED` or `SCHEMA_FAILED`.

## Safety Gates
- `PRODUCTION SAFETY GATE`: Destructive or unconfirmed commands are blocked in `production` environments.
- Credentials must exist in `.env` to execute provisioning. If blocked, the system reports `BLOCKED` rather than faking success.
