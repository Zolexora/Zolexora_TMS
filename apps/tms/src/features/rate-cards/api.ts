import { apiClient } from '../../lib/api';

export interface RateCardRule {
  rule_type: string;
  name: string;
  base_amount: number;
  quantity_included: number;
  rate_per_unit: number;
  is_percentage: boolean;
  percentage_value: number;
  sequence: number;
}

export interface RateCard {
  id: string;
  name: string;
  side: 'CUSTOMER' | 'VENDOR';
  service_type: string;
  customer_id?: string;
  vendor_id?: string;
  active: boolean;
}

export const createRateCard = async (payload: any): Promise<RateCard> => {
  return apiClient<RateCard>('/api/v1/rate-cards', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
};
