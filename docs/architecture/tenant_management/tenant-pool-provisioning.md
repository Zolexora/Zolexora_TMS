# Tenant Pool Provisioning
Provisioning scripts in `app.cli.tenant_pool` securely interface with provider APIs. Idempotent design ensures slots 001-010 are safely updated without duplication. Failed provisioning operations are marked as BLOCKED, not READY.
