import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getRequirements,
  createRequirement,
  getRecords,
  createOrUpdateRecord,
  verifyRecord, waiveRecord,
  evaluateCompliance,
  ComplianceEntityType,
  ComplianceStatus,
  ComplianceRequirement,
  ComplianceRecord
} from './api';

export const useComplianceRequirements = (entityType?: ComplianceEntityType) => {
  return useQuery({
    queryKey: ['compliance', 'requirements', entityType],
    queryFn: () => getRequirements(entityType),
  });
};

export const useCreateComplianceRequirement = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<ComplianceRequirement>) => createRequirement(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compliance', 'requirements'] });
    },
  });
};

export const useComplianceRecords = (params?: { entity_type?: ComplianceEntityType; entity_id?: string; status?: ComplianceStatus }) => {
  return useQuery({
    queryKey: ['compliance', 'records', params],
    queryFn: () => getRecords(params),
  });
};

export const useUpdateComplianceRecord = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<ComplianceRecord>) => createOrUpdateRecord(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['compliance', 'records'] });
      if (variables.entity_id) {
        queryClient.invalidateQueries({ queryKey: ['compliance', 'evaluate'] });
      }
    },
  });
};

export const useVerifyComplianceRecord = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, method, comments }: { id: string; method?: string; comments?: string }) => verifyRecord(id, method, comments),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compliance', 'records'] });
      queryClient.invalidateQueries({ queryKey: ['compliance', 'evaluate'] });
    },
  });
};

export const useComplianceEvaluation = (params: {
  vehicle_id?: string;
  driver_id?: string;
  vendor_id?: string;
  customer_id?: string;
  service_type?: string;
  state_code?: string;
}) => {
  return useQuery({
    queryKey: ['compliance', 'evaluate', params],
    queryFn: () => evaluateCompliance(params),
    enabled: !!(params.vehicle_id || params.driver_id || params.vendor_id || params.customer_id),
  });
};

export const useWaiveComplianceRecord = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason, valid_until }: { id: string; reason: string; valid_until: string }) => waiveRecord(id, reason, valid_until),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compliance', 'records'] });
      queryClient.invalidateQueries({ queryKey: ['compliance', 'evaluate'] });
    },
  });
};
