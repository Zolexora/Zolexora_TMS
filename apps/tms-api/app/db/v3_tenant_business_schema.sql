-- Phase 7: Full Business Schema Migration for D1 Tenant Data Plane

-- 1. Trips
CREATE TABLE IF NOT EXISTS trips (
    id TEXT PRIMARY KEY,
    trip_number TEXT NOT NULL UNIQUE,
    duty_id TEXT NOT NULL UNIQUE,
    driver_id TEXT NOT NULL,
    vehicle_id TEXT NOT NULL,
    start_odometer REAL NOT NULL,
    end_odometer REAL,
    total_distance_km REAL,
    start_timestamp DATETIME,
    end_timestamp DATETIME,
    start_location TEXT DEFAULT '{}',
    end_location TEXT DEFAULT '{}',
    toll_amount REAL DEFAULT 0.0,
    fuel_amount REAL DEFAULT 0.0,
    parking_amount REAL DEFAULT 0.0,
    waiting_minutes INTEGER DEFAULT 0,
    status TEXT DEFAULT 'NOT_STARTED',
    pod_attachment_url TEXT,
    pod_notes TEXT,
    pod_uploaded_at DATETIME,
    operational_receipts TEXT DEFAULT '[]',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(duty_id) REFERENCES duties(id),
    FOREIGN KEY(driver_id) REFERENCES drivers(id),
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
);

CREATE TABLE IF NOT EXISTS trip_events (
    id TEXT PRIMARY KEY,
    trip_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    latitude REAL,
    longitude REAL,
    notes TEXT,
    FOREIGN KEY(trip_id) REFERENCES trips(id) ON DELETE CASCADE
);

-- 2. Invoices
CREATE TABLE IF NOT EXISTS invoice_lines (
    id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL,
    description TEXT NOT NULL,
    quantity REAL NOT NULL DEFAULT 1.0,
    unit_price REAL NOT NULL,
    amount REAL NOT NULL,
    sac_code TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS invoice_tax_lines (
    id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL,
    tax_name TEXT NOT NULL,
    tax_rate REAL NOT NULL,
    tax_amount REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS financial_adjustment_notes (
    id TEXT PRIMARY KEY,
    note_number TEXT NOT NULL UNIQUE,
    invoice_id TEXT NOT NULL,
    note_type TEXT NOT NULL, -- CREDIT, DEBIT
    status TEXT DEFAULT 'DRAFT',
    reason TEXT,
    subtotal REAL NOT NULL,
    tax_total REAL NOT NULL,
    total_amount REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);

-- 3. Payables & Settlements (Vendor Payments)
CREATE TABLE IF NOT EXISTS payables (
    id TEXT PRIMARY KEY,
    payable_number TEXT NOT NULL UNIQUE,
    vendor_id TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT DEFAULT 'DRAFT',
    due_date DATETIME,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(vendor_id) REFERENCES vendors(id)
);

CREATE TABLE IF NOT EXISTS payable_lines (
    id TEXT PRIMARY KEY,
    payable_id TEXT NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL,
    duty_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(payable_id) REFERENCES payables(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settlements (
    id TEXT PRIMARY KEY,
    settlement_number TEXT NOT NULL UNIQUE,
    vendor_id TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT DEFAULT 'PENDING',
    settlement_date DATETIME,
    payment_reference TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(vendor_id) REFERENCES vendors(id)
);

-- 4. Payments (Customer Payments)
CREATE TABLE IF NOT EXISTS payment_allocations (
    id TEXT PRIMARY KEY,
    payment_id TEXT NOT NULL,
    invoice_id TEXT NOT NULL,
    amount_allocated REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(payment_id) REFERENCES payments(id) ON DELETE CASCADE,
    FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);

-- 5. Rate Cards
CREATE TABLE IF NOT EXISTS rate_card_versions (
    id TEXT PRIMARY KEY,
    rate_card_id TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    effective_from DATETIME NOT NULL,
    effective_to DATETIME,
    base_rate REAL NOT NULL,
    status TEXT DEFAULT 'DRAFT',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(rate_card_id) REFERENCES rate_cards(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rate_card_rules (
    id TEXT PRIMARY KEY,
    rate_card_version_id TEXT NOT NULL,
    rule_type TEXT NOT NULL,
    parameter TEXT,
    threshold REAL,
    rate REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(rate_card_version_id) REFERENCES rate_card_versions(id) ON DELETE CASCADE
);

-- 6. Expenses
CREATE TABLE IF NOT EXISTS expenses (
    id TEXT PRIMARY KEY,
    expense_number TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    expense_date DATETIME NOT NULL,
    vehicle_id TEXT,
    driver_id TEXT,
    duty_id TEXT,
    receipt_url TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 7. PL / Financial Snapshots
CREATE TABLE IF NOT EXISTS financial_periods (
    id TEXT PRIMARY KEY,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    status TEXT DEFAULT 'OPEN',
    closed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS financial_snapshots (
    id TEXT PRIMARY KEY,
    snapshot_date DATETIME NOT NULL,
    total_revenue REAL NOT NULL DEFAULT 0,
    total_cogs REAL NOT NULL DEFAULT 0,
    total_expenses REAL NOT NULL DEFAULT 0,
    gross_margin REAL NOT NULL DEFAULT 0,
    net_margin REAL NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO schema_migrations (version) VALUES (3);
