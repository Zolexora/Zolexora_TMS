-- Phase 7: Booking Lifecycle Schema Expansion for D1
-- Expands the D1 tenant database to support robust Booking Requests, Bookings, and Duties.

-- 1. Create Booking Requests
CREATE TABLE IF NOT EXISTS booking_requests (
    id TEXT PRIMARY KEY,
    booking_request_number TEXT NOT NULL UNIQUE,
    customer_id TEXT NOT NULL,
    service_type TEXT NOT NULL,
    pickup_address TEXT NOT NULL,
    drop_address TEXT NOT NULL,
    pickup_datetime DATETIME NOT NULL,
    passenger_info TEXT DEFAULT '{}',
    vehicle_requirements TEXT DEFAULT '{}',
    special_requirements TEXT,
    pricing_context TEXT DEFAULT '{}',
    status TEXT DEFAULT 'PENDING',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(customer_id) REFERENCES customers(id)
);

-- 2. Alter Bookings table
-- SQLite doesn't support DROP COLUMN or ALTER COLUMN heavily, so we'll just add the necessary columns.
-- For a fresh or largely empty dev DB, we can recreate it, but ALTER TABLE ADD COLUMN is safer if there is data.
-- Actually, there is NO data yet in the remote D1 tables, so we can DROP and RECREATE or just ADD. Let's recreate.
DROP TABLE IF EXISTS bookings;
CREATE TABLE bookings (
    id TEXT PRIMARY KEY,
    booking_number TEXT NOT NULL UNIQUE,
    booking_request_id TEXT,
    customer_id TEXT NOT NULL,
    service_type TEXT NOT NULL,
    pickup_address TEXT NOT NULL,
    pickup_lat REAL,
    pickup_lng REAL,
    drop_address TEXT NOT NULL,
    drop_lat REAL,
    drop_lng REAL,
    pickup_datetime DATETIME NOT NULL,
    expected_completion_datetime DATETIME,
    passenger_info TEXT DEFAULT '{}',
    vehicle_requirements TEXT DEFAULT '{}',
    rate_card_version_id TEXT,
    commercial_terms TEXT DEFAULT '{}',
    operational_instructions TEXT,
    status TEXT DEFAULT 'CONFIRMED',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(booking_request_id) REFERENCES booking_requests(id),
    FOREIGN KEY(customer_id) REFERENCES customers(id)
);

-- 3. Alter Duties table
DROP TABLE IF EXISTS duties;
CREATE TABLE duties (
    id TEXT PRIMARY KEY,
    duty_number TEXT NOT NULL UNIQUE,
    booking_id TEXT NOT NULL,
    driver_id TEXT,
    vehicle_id TEXT,
    scheduled_start_time DATETIME NOT NULL,
    scheduled_end_time DATETIME,
    start_time DATETIME,
    end_time DATETIME,
    start_km REAL,
    end_km REAL,
    status TEXT DEFAULT 'UNASSIGNED',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(booking_id) REFERENCES bookings(id),
    FOREIGN KEY(driver_id) REFERENCES drivers(id),
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
);

-- 4. Audit Trail / Events for Duty Transitions
CREATE TABLE IF NOT EXISTS duty_events (
    id TEXT PRIMARY KEY,
    duty_id TEXT NOT NULL,
    actor_id TEXT,
    event_type TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT,
    event_metadata TEXT DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(duty_id) REFERENCES duties(id)
);

-- 5. Operational Expenses (Fuel, Tolls, Batta)
CREATE TABLE IF NOT EXISTS operational_expenses (
    id TEXT PRIMARY KEY,
    duty_id TEXT NOT NULL,
    expense_type TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'INR',
    expense_date DATETIME NOT NULL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(duty_id) REFERENCES duties(id)
);

INSERT OR IGNORE INTO schema_migrations (version) VALUES (2);
