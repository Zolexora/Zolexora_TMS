export interface Company {
  code: string;
  name: string;
  currency: string;
  fiscal_year_start: string;
  legal_name?: string | null;
  business_type?: string | null;
  gst_number?: string | null;
  pan_number?: string | null;
  registered_address?: string | null;
  logo_object_key?: string | null;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Site {
  id: string;
  company_code: string;
  business_unit_id: string;
  site_code: string;
  site_name: string;
  address: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Client {
  id: string;
  company_code: string;
  client_code: string;
  client_name: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export type FinancialPeriodStatus = 'open' | 'closed' | 'locked';

export interface FinancialYear {
  id: string;
  company_code: string;
  name: string;
  start_date: string;
  end_date: string;
  status: 'active' | 'closed';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface FinancialPeriod {
  id: string;
  company_code: string;
  financial_year_id: string;
  month_number: number;
  period_code: string;
  start_date: string;
  end_date: string;
  status: FinancialPeriodStatus;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  status_before_lock?: 'open' | 'closed' | null;
}

export interface PLGroup {
  id: string;
  company_code?: string | null;
  code?: string;
  name: string;
  group_type?: PLGroupType;
  parent_id: string | null;
  display_order: number;
  normal_direction: 'debit' | 'credit';
  is_system?: boolean;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export type PLGroupType = 'income' | 'direct_expense' | 'indirect_expense' | 'other_income' | 'finance_cost' | 'depreciation' | 'tax';

export interface AccountMaster {
  id: string;
  code: string;
  name: string;
  company_code: string;
  pl_group_id: string | null;
  normal_direction: 'debit' | 'credit';
  display_order: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface EntryBatch {
  id: string;
  company_code: string;
  period: string; // YYYY-MM
  status: 'draft' | 'posted';
  business_unit_id?: string | null;
  site_id?: string | null;
  client_id?: string | null;
  vehicle_id?: string | null;
  manager_id?: string | null;
  created_at: string;
  posted_at: string | null;
  batch_type: 'standard' | 'reversal' | 'adjustment';
}

export interface LedgerEntry {
  id: string;
  batch_id: string;
  account_code: string;
  debit: number;
  credit: number;
  description: string | null;
}

export interface AuditLog {
  id: number;
  timestamp: string;
  user_email: string;
  role: string;
  action: string;
  details: string;
}

export interface ImportValidationTemp {
  id: string;
  company_code: string;
  status: 'validating' | 'valid' | 'failed';
  error_summary: string | null;
  created_at: string;
}
