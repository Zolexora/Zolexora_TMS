import { apiClient } from '@/lib/api';

export type ComplianceCategory = 'STATUTORY' | 'CONTRACTUAL' | 'INTERNAL' | 'SAFETY';
export type ComplianceEntityType = 'ORGANISATION' | 'VEHICLE' | 'DRIVER' | 'VENDOR' | 'CUSTOMER' | 'SERVICE' | 'ROUTE' | 'DUTY';
export type ComplianceStatus = 'MISSING' | 'PENDING' | 'VERIFICATION_REQUIRED' | 'VALID' | 'EXPIRING_SOON' | 'EXPIRED' | 'REJECTED' | 'WAIVED';

export interface ComplianceRequirement {
  id: string;
  organisation_id: string | null;
  code: string;
  name: string;
  description?: string;
  category: ComplianceCategory;
  entity_type: ComplianceEntityType;
  document_type?: string;
  mandatory: boolean;
  blocking: boolean;
  verification_required: boolean;
  validity_period_days?: number;
  active: boolean;
  source_reference?: string;
  notes?: string;
  conditions?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ComplianceRecord {
  id: string;
  organisation_id: string;
  requirement_id: string;
  entity_type: ComplianceEntityType;
  entity_id: string;
  status: ComplianceStatus;
  document_number?: string;
  document_url?: string;
  original_filename?: string;
  mime_type?: string;
  issued_date?: string;
  expiry_date?: string;
  verified_at?: string;
  verified_by?: string;
  verification_method?: string;
  rejection_reason?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ComplianceIssue {
  code: string;
  category: ComplianceCategory;
  severity: 'BLOCK' | 'WARNING';
  entity_type: ComplianceEntityType;
  entity_id: string;
  requirement_id: string;
  message: string;
  document_id?: string;
  expires_at?: string;
}

export interface ComplianceEvaluation {
  status: 'PASS' | 'WARNING' | 'BLOCK';
  evaluated_at: string;
  blocking_issues: ComplianceIssue[];
  warnings: ComplianceIssue[];
  valid_requirements: string[];
  missing_requirements: string[];
  expired_requirements: string[];
  verification_required: string[];
  rule_versions: string[];
}

export const getRequirements = async (entityType?: ComplianceEntityType): Promise<ComplianceRequirement[]> => {
  const url = entityType ? `/api/v1/compliance/requirements?entity_type=${entityType}` : '/api/v1/compliance/requirements';
  return apiClient<ComplianceRequirement[]>(url);
};

export const createRequirement = async (data: Partial<ComplianceRequirement>): Promise<ComplianceRequirement> => {
  return apiClient<ComplianceRequirement>('/api/v1/compliance/requirements', {
    method: 'POST',
    body: JSON.stringify(data)
  });
};

export const getRecords = async (params?: { entity_type?: ComplianceEntityType; entity_id?: string; status?: ComplianceStatus }): Promise<ComplianceRecord[]> => {
  const searchParams = new URLSearchParams();
  if (params?.entity_type) searchParams.append('entity_type', params.entity_type);
  if (params?.entity_id) searchParams.append('entity_id', params.entity_id);
  if (params?.status) searchParams.append('status', params.status);
  
  const url = `/api/v1/compliance/records?${searchParams.toString()}`;
  return apiClient<ComplianceRecord[]>(url);
};

export const createOrUpdateRecord = async (data: Partial<ComplianceRecord>): Promise<ComplianceRecord> => {
  return apiClient<ComplianceRecord>('/api/v1/compliance/records', {
    method: 'POST',
    body: JSON.stringify(data)
  });
};

export const verifyRecord = async (recordId: string, method: string = 'MANUAL', comments?: string): Promise<ComplianceRecord> => {
  return apiClient<ComplianceRecord>(`/api/v1/compliance/records/${recordId}/verify`, {
    method: 'POST',
    body: JSON.stringify({ method, comments })
  });
};

export const evaluateCompliance = async (params: {
  vehicle_id?: string;
  driver_id?: string;
  vendor_id?: string;
  customer_id?: string;
  service_type?: string;
  state_code?: string;
}): Promise<ComplianceEvaluation> => {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) searchParams.append(key, value);
  });
  
  return apiClient<ComplianceEvaluation>(`/api/v1/compliance/evaluate?${searchParams.toString()}`);
};

export const waiveRecord = async (recordId: string, reason: string, valid_until: string): Promise<ComplianceRecord> => {
  return apiClient<ComplianceRecord>(`/api/v1/compliance/records/${recordId}/waive`, {
    method: 'POST',
    body: JSON.stringify({ reason, valid_until })
  });
};
