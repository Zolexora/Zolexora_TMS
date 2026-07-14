-- ZolexoraERP Lite -- Supabase Postgres schema (masters + auth-adjacent data)
--
-- This is a fresh, consolidated schema for the new split architecture, not a
-- replay of the original SQLite/D1 migration history. A few deliberate
-- differences from the original D1 schema:
--   * Table/column names are lowercase (Postgres convention) instead of the
--     original mixed-case (Companies, PL_Groups, Account_Master, ...).
--   * is_active / boolean-ish integer columns are native BOOLEAN here.
--   * `users` / `roles` / `user_roles` are replaced by `user_profiles`
--     (keyed by the Supabase Auth user id) with a single `role` column --
--     the app only ever exposed one role per session, so the extra join
--     table added no real flexibility.
--   * Foreign keys that used to point at Entry_Batches/Ledger_Entries (now
--     in Cloudflare D1) cannot exist here -- referential integrity for
--     those relationships is enforced by the FastAPI service layer instead
--     of the database. See the top-level README's "Architecture tradeoffs"
--     section.

create extension if not exists pgcrypto;

create table if not exists companies (
  code text primary key,
  name text not null,
  currency text not null default 'USD',
  fiscal_year_start text not null default '01-01',
  legal_name text not null,
  business_type text,
  gst_number text,
  pan_number text,
  registered_address text,
  logo_object_key text,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists business_units (
  id text primary key,
  company_code text not null references companies(code) on delete restrict,
  code text not null,
  name text not null,
  business_type text not null,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (company_code, code)
);

create table if not exists sites (
  id text primary key,
  company_code text not null references companies(code) on delete restrict,
  business_unit_id text not null references business_units(id) on delete restrict,
  site_code text not null,
  site_name text not null,
  address text,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (company_code, site_code)
);

create table if not exists clients (
  id text primary key,
  company_code text not null references companies(code) on delete restrict,
  client_code text not null,
  client_name text not null,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (company_code, client_code)
);

create table if not exists managers (
  id text primary key,
  company_code text not null references companies(code) on delete restrict,
  manager_code text not null,
  manager_name text not null,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (company_code, manager_code)
);

create table if not exists ownership_types (
  id text primary key,
  company_code text not null references companies(code) on delete restrict,
  code text not null,
  name text not null,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (company_code, code)
);

create table if not exists vehicle_models (
  id text primary key,
  company_code text not null references companies(code) on delete restrict,
  model_code text not null,
  model_name text not null,
  vehicle_type text not null,
  default_ideal_avg integer not null,
  penalty_trigger_avg integer not null,
  penalty_base_avg integer not null,
  effective_from text not null,
  effective_to text,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (company_code, model_code, effective_from)
);

create table if not exists vehicles (
  id text primary key,
  company_code text not null references companies(code) on delete restrict,
  registration_number text not null,
  ownership_id text not null references ownership_types(id) on delete restrict,
  vehicle_model_id text not null references vehicle_models(id) on delete restrict,
  vehicle_type text not null,
  allocated_site_id text not null references sites(id) on delete restrict,
  default_manager_id text not null references managers(id) on delete restrict,
  is_emi_applicable boolean not null default false,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (company_code, registration_number)
);

create table if not exists pl_groups (
  id text primary key,
  company_code text references companies(code) on delete restrict,
  code text not null,
  name text not null,
  group_type text not null check (group_type in ('income', 'direct_expense', 'indirect_expense', 'other_income', 'finance_cost', 'depreciation', 'tax')),
  parent_id text references pl_groups(id) on delete restrict,
  display_order integer not null default 0,
  normal_direction text not null check (normal_direction in ('debit', 'credit')),
  is_system boolean not null default false,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index if not exists uq_pl_groups_company_code on pl_groups (company_code, code) where company_code is not null;

create table if not exists account_master (
  id text primary key,
  code text not null,
  company_code text not null references companies(code) on delete restrict,
  name text not null,
  pl_group_id text references pl_groups(id) on delete restrict,
  normal_direction text not null check (normal_direction in ('debit', 'credit')),
  display_order integer not null default 0,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (company_code, code)
);

create table if not exists financial_years (
  id text primary key,
  company_code text not null references companies(code) on delete restrict,
  name text not null,
  start_date text not null,
  end_date text not null,
  status text not null default 'active' check (status in ('active', 'closed')),
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (company_code, name)
);

create table if not exists financial_periods (
  id text primary key,
  company_code text not null references companies(code) on delete restrict,
  financial_year_id text not null references financial_years(id) on delete restrict,
  month_number integer not null,
  period_code text not null,
  status text not null check (status in ('open', 'closed', 'locked')),
  status_before_lock text check (status_before_lock in ('open', 'closed') or status_before_lock is null),
  is_active boolean not null default true,
  start_date text,
  end_date text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (company_code, period_code),
  unique (financial_year_id, month_number)
);

-- Auth-adjacent: profile + company-access grants, keyed by the Supabase
-- Auth user id (auth.users.id). We deliberately do NOT put a foreign key on
-- auth.users here -- cross-schema FKs into Supabase's managed auth schema
-- are unnecessary and the row is provisioned lazily on first API call
-- anyway (see app/core/security.py:_load_profile).
create table if not exists user_profiles (
  auth_user_id text primary key,
  email text not null,
  full_name text,
  role text not null default 'Viewer' check (role in ('Admin', 'FinanceAdmin', 'Accountant', 'DataEntry', 'Viewer', 'Auditor')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists user_company_access (
  id text primary key,
  auth_user_id text not null references user_profiles(auth_user_id) on delete cascade,
  company_code text not null references companies(code) on delete cascade,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (auth_user_id, company_code)
);

create index if not exists idx_sites_company on sites(company_code);
create index if not exists idx_clients_company on clients(company_code);
create index if not exists idx_managers_company on managers(company_code);
create index if not exists idx_vehicles_company on vehicles(company_code);
create index if not exists idx_account_master_company on account_master(company_code, is_active);
create index if not exists idx_pl_groups_company on pl_groups(company_code, display_order);
create index if not exists idx_financial_years_company_dates on financial_years(company_code, start_date, end_date, is_active);
create index if not exists idx_financial_periods_company_status on financial_periods(company_code, period_code, status, is_active);
create index if not exists idx_financial_periods_year on financial_periods(financial_year_id, month_number);
create index if not exists idx_user_company_access_user on user_company_access(auth_user_id, is_active);
