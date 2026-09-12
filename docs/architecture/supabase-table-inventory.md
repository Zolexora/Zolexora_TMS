# Supabase Table Inventory

## Control Plane Tables
| Table | Purpose | Referenced By | Action |
|-------|---------|---------------|--------|
| `organisations` | Core tenant identity | Backend, Auth | **KEEP** |
| `organisation_members` | Tenant membership & RBAC | Backend, RLS | **KEEP** |
| `roles` | RBAC roles | Backend, Auth | **KEEP** |
| `permissions` | RBAC permissions | Backend | **KEEP** |
| `role_permissions` | RBAC mapping | Backend | **KEEP** |
| `profiles` | User profiles extending Auth | Backend, RLS | **KEEP** |
| `platform_audit_logs` | Platform telemetry | Backend | **KEEP** |
| `tenant_database_registry` | D1 tracking | Migration, Backend | **KEEP** |
| `organisation_database_assignments` | Tenant D1 assignment | Backend | **KEEP** |
| `tenant_mongodb_registry` | Atlas tracking | Migration, Backend | **KEEP** |
| `organisation_mongodb_assignments` | Tenant Atlas assignment | Backend | **KEEP** |
| `organisation_storage_assignments` | R2/Cloudinary assignment | Backend | **KEEP** |
| `tenant_migration_jobs` | Pilot tracking | Migration Service | **KEEP** |

## Tenant Data Plane Tables (PostgreSQL Fallback Architecture)
| Table | Purpose | Referenced By | Action |
|-------|---------|---------------|--------|
| `customers` | Master data | `app/modules/customers/` | **REVIEW** |
| `vehicles` | Master data | `app/modules/vehicles/` | **REVIEW** |
| `drivers` | Master data | `app/modules/drivers/` | **REVIEW** |
| `vendors` | Master data | `app/modules/vendors/` | **REVIEW** |
| `bookings` | Operations | `app/modules/bookings/` | **REVIEW** |
| `booking_requests` | Operations | `app/modules/bookings/` | **REVIEW** |
| `duties` | Operations | `app/modules/duties/` | **REVIEW** |
| `duty_assignments` | Operations | `app/modules/duties/` | **REVIEW** |
| `trips` | Operations | `app/modules/trips/` | **REVIEW** |
| `trip_events` | Operations | `app/modules/trips/` | **REVIEW** |
| `rate_cards` | Financials | `app/modules/billing/` | **REVIEW** |
| `rate_card_versions` | Financials | `app/modules/billing/` | **REVIEW** |
| `rate_card_rules` | Financials | `app/modules/billing/` | **REVIEW** |
| `invoices` | Financials | `app/modules/invoices/` | **REVIEW** |
| `invoice_lines` | Financials | `app/modules/invoices/` | **REVIEW** |
| `invoice_tax_lines` | Financials | `app/modules/invoices/` | **REVIEW** |
| `payments` | Financials | `app/modules/payments/` | **REVIEW** |
| `payment_allocations` | Financials | `app/modules/payments/` | **REVIEW** |
| `payment_events` | Financials | `app/modules/payments/` | **REVIEW** |
| `payables` | Financials | `app/modules/payables/` | **REVIEW** |
| `payable_lines` | Financials | `app/modules/payables/` | **REVIEW** |
| `settlements` | Financials | `app/modules/payables/` | **REVIEW** |
| `vendor_settlement_statements`| Financials | `app/modules/payables/`| **REVIEW** |
| `expenses` | Financials | `app/modules/expenses/` | **REVIEW** |
| `financial_snapshots` | Financials | `app/modules/billing/` | **REVIEW** |
| `financial_snapshot_lines` | Financials | `app/modules/billing/` | **REVIEW** |
| `billing_records` | Financials | `app/modules/billing/` | **REVIEW** |
| `financial_periods` | Financials | `app/modules/pl/` | **REVIEW** |
| `financial_audit_logs` | Financials | `app/modules/pl/` | **REVIEW** |
| `financial_adjustment_notes` | Financials | `app/modules/invoices/` | **REVIEW** |
| `financial_adjustment_note_lines`| Financials| `app/modules/invoices/` | **REVIEW** |
| `financial_adjustment_note_tax_lines`| Financials | `app/modules/invoices/` | **REVIEW** |
| `compliance_requirements` | Compliance | `app/modules/compliance/` | **REVIEW** |
| `compliance_records` | Compliance | `app/modules/compliance/` | **REVIEW** |
| `compliance_verifications` | Compliance | `app/modules/compliance/` | **REVIEW** |
| `audit_logs` | Operations | `app/modules/audit/` | **REVIEW** |
