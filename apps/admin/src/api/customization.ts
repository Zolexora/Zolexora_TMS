import { apiClient } from '../lib/api';

/**
 * Foundation for Zolexora Platform Admin Customization Endpoints.
 * 
 * Phase 6.6 establishes these integration points for future admin panel expansion.
 * The endpoints allow Platform Admins to query and manage application definitions across tenants.
 */

export interface OrganisationApplication {
  id: string;
  organisation_id: string;
  application_type: 'STANDARD' | 'CONFIGURED' | 'EXTENDED' | 'CUSTOM';
  application_name: string;
  application_version: string;
  status: 'DRAFT' | 'ACTIVE' | 'DEPRECATED' | 'ARCHIVED';
}

export const customizationApi = {
  // Query all applications globally (requires Platform Admin)
  getApplications: () => apiClient<OrganisationApplication[]>('/api/v1/platform/applications'),
  
  // Get detailed configuration for a specific tenant
  getTenantRuntime: (organisationId: string) => 
    apiClient<any>(`/api/v1/platform/applications/${organisationId}/runtime`),
    
  // Update configuration (Future capability)
  updateConfiguration: (organisationId: string, payload: any) => 
    apiClient<any>(`/api/v1/platform/applications/${organisationId}/config`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
};
