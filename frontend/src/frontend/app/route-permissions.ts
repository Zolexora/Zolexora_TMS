import type { UserRole } from '../../shared/types';
import type { RoutePath } from './router';

export const ROUTE_ROLES: Partial<Record<RoutePath, UserRole[]>> = {
  '/dashboard': ['Admin', 'FinanceAdmin', 'Accountant', 'DataEntry', 'Viewer', 'Auditor'],
  '/companies': ['Admin'],
  '/periods': ['Admin', 'FinanceAdmin', 'Accountant'],
  '/groups': ['Admin', 'FinanceAdmin'],
  '/accounts': ['Admin', 'FinanceAdmin', 'Accountant', 'Viewer', 'Auditor'],
  '/manual-entry': ['Admin', 'FinanceAdmin', 'Accountant', 'DataEntry'],
  '/entry-history': ['Admin', 'FinanceAdmin', 'Accountant', 'DataEntry', 'Viewer', 'Auditor'],
  '/bulk-upload': ['Admin', 'FinanceAdmin', 'Accountant', 'DataEntry'],
  '/import-history': ['Admin', 'FinanceAdmin', 'Accountant', 'DataEntry', 'Viewer', 'Auditor'],
  '/reports': ['Admin', 'FinanceAdmin', 'Accountant', 'Viewer', 'Auditor'],
  '/comparison': ['Admin', 'FinanceAdmin', 'Accountant', 'Viewer', 'Auditor'],
  '/audit-logs': ['Admin', 'FinanceAdmin', 'Auditor'],
  '/settings': ['Admin', 'FinanceAdmin'],
};
