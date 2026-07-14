-- ZolexoraERP Lite -- Cloudflare D1 schema (transactional data only)
--
-- This keeps the original table/column names and types (SQLite dialect,
-- mixed-case identifiers) since this D1 database is unchanged from the
-- application's point of view -- only the *masters* tables moved out.
--
-- IMPORTANT: foreign keys that used to reference Companies/business_units/
-- sites/clients/vehicles/managers are removed here because those tables no
-- longer live in this database (they're in Supabase Postgres now). D1/
-- SQLite cannot enforce a foreign key against a table in a different
-- database. Referential integrity for those relationships is enforced
-- entirely by the FastAPI service layer (see entries/service.py, which
-- resolves and validates every dimension against Postgres before writing
-- here) -- any code path that writes to this database bypassing FastAPI
-- would not get that protection. Self-referential FKs (original_batch_id /
-- reversal_batch_id, both pointing at Entry_Batches.id) are kept since both
-- sides are still in this database.

CREATE TABLE IF NOT EXISTS Entry_Batches (
    id TEXT PRIMARY KEY,
    company_code TEXT NOT NULL,
    period TEXT NOT NULL CHECK(length(period) = 7 AND period LIKE '____-__'),
    status TEXT NOT NULL CHECK(status IN ('draft', 'posted')),
    batch_type TEXT NOT NULL CHECK(batch_type IN ('standard', 'reversal', 'adjustment')),
    business_unit_id TEXT,
    site_id TEXT,
    client_id TEXT,
    vehicle_id TEXT,
    manager_id TEXT,
    reference TEXT,
    description TEXT,
    created_by TEXT,
    posted_by TEXT,
    posted_at TEXT,
    idempotency_key TEXT,
    original_batch_id TEXT,
    reversal_batch_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (original_batch_id) REFERENCES Entry_Batches(id) ON DELETE SET NULL,
    FOREIGN KEY (reversal_batch_id) REFERENCES Entry_Batches(id) ON DELETE SET NULL,
    CONSTRAINT uq_entry_batches_idempotency UNIQUE (idempotency_key)
);

CREATE TABLE IF NOT EXISTS Ledger_Entries (
    id TEXT NOT NULL PRIMARY KEY,
    batch_id TEXT NOT NULL,
    company_code TEXT NOT NULL,
    account_code TEXT NOT NULL,
    debit INTEGER NOT NULL DEFAULT 0 CHECK(debit >= 0),
    credit INTEGER NOT NULL DEFAULT 0 CHECK(credit >= 0),
    description TEXT,
    FOREIGN KEY (batch_id) REFERENCES Entry_Batches(id) ON DELETE CASCADE,
    CONSTRAINT check_debit_credit CHECK (debit > 0 OR credit > 0),
    CONSTRAINT check_mutually_exclusive CHECK (debit = 0 OR credit = 0)
);

CREATE TABLE IF NOT EXISTS Audit_Logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    user_email TEXT NOT NULL,
    role TEXT NOT NULL,
    action TEXT NOT NULL,
    details TEXT
);

CREATE TABLE IF NOT EXISTS import_jobs (
    id TEXT PRIMARY KEY,
    company_code TEXT NOT NULL,
    filename TEXT NOT NULL,
    import_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('uploaded', 'parsing', 'validating', 'review_required', 'ready', 'importing', 'completed', 'failed', 'cancelled')),
    error_summary TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS import_rows (
    id TEXT PRIMARY KEY,
    import_job_id TEXT NOT NULL,
    row_number INTEGER NOT NULL,
    raw_data TEXT NOT NULL,
    normalized_data TEXT,
    validation_status TEXT NOT NULL CHECK(validation_status IN ('validating', 'valid', 'failed', 'warning')),
    validation_errors TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (import_job_id) REFERENCES import_jobs(id) ON DELETE CASCADE,
    UNIQUE(import_job_id, row_number)
);

CREATE INDEX IF NOT EXISTS idx_entry_batches_company_period ON Entry_Batches(company_code, period);
CREATE INDEX IF NOT EXISTS idx_entry_batches_site ON Entry_Batches(site_id);
CREATE INDEX IF NOT EXISTS idx_entry_batches_client ON Entry_Batches(client_id);
CREATE INDEX IF NOT EXISTS idx_entry_batches_vehicle ON Entry_Batches(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_entry_batches_manager ON Entry_Batches(manager_id);
CREATE INDEX IF NOT EXISTS idx_entry_batches_idempotency ON Entry_Batches(idempotency_key);
CREATE INDEX IF NOT EXISTS idx_entry_batches_created_at ON Entry_Batches(created_at);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_batch ON Ledger_Entries(batch_id);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_account ON Ledger_Entries(company_code, account_code);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON Audit_Logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_import_rows_job ON import_rows(import_job_id);
