import React, { createContext, useCallback, useContext, useMemo, useState, useEffect } from 'react';
import type { UserRole } from '../../shared/types';
import { AccountsPage } from '../features/accounts/pages/AccountsPage';
import { CompaniesPage } from '../features/companies/pages/CompaniesPage';
import { PeriodsPage } from '../features/periods/pages/PeriodsPage';
import { PnlGroupsPage } from '../features/pnl-groups/pages/PnlGroupsPage';
import { AppLayout } from '../layouts/AppLayout';
import { ROUTE_ROLES } from './route-permissions';
import { DashboardPage } from '../features/dashboard/pages/DashboardPage';
import { ManualEntryPage } from '../features/entries/pages/ManualEntryPage';
import { EntryHistoryPage } from '../features/entries/pages/EntryHistoryPage';
import { BulkUploadPage } from '../features/imports/pages/BulkUploadPage';
import { ImportHistoryPage } from '../features/imports/pages/ImportHistoryPage';
import { ReportsPage } from '../features/reports/pages/ReportsPage';
import { CompanyComparisonPage } from '../features/reports/pages/CompanyComparisonPage';
import { AuditLogsPage } from '../features/audit/pages/AuditLogsPage';
import { SettingsPage } from '../features/settings/pages/SettingsPage';

export type RoutePath = 
  | '/login'
  | '/dashboard'
  | '/companies'
  | '/periods'
  | '/groups'
  | '/accounts'
  | '/manual-entry'
  | '/entry-history'
  | '/bulk-upload'
  | '/import-history'
  | '/reports'
  | '/comparison'
  | '/audit-logs'
  | '/settings';

export type AuthenticatedRoutePath = Exclude<RoutePath, '/login'>;

export const VALID_ROUTES: readonly RoutePath[] = [
  '/login',
  '/dashboard',
  '/companies',
  '/periods',
  '/groups',
  '/accounts',
  '/manual-entry',
  '/entry-history',
  '/bulk-upload',
  '/import-history',
  '/reports',
  '/comparison',
  '/audit-logs',
  '/settings',
] as const;

export const PAGE_COMPONENTS: Record<AuthenticatedRoutePath, React.ComponentType> = {
  '/dashboard': DashboardPage,
  '/companies': CompaniesPage,
  '/periods': PeriodsPage,
  '/groups': PnlGroupsPage,
  '/accounts': AccountsPage,
  '/manual-entry': ManualEntryPage,
  '/entry-history': EntryHistoryPage,
  '/bulk-upload': BulkUploadPage,
  '/import-history': ImportHistoryPage,
  '/reports': ReportsPage,
  '/comparison': CompanyComparisonPage,
  '/audit-logs': AuditLogsPage,
  '/settings': SettingsPage,
};

export function resolveInitialRoute(hash: string, hasToken: boolean): RoutePath {
  const path = hash.startsWith('#') ? hash.slice(1) : hash;
  return VALID_ROUTES.includes(path as RoutePath)
    ? path as RoutePath
    : hasToken ? '/dashboard' : '/login';
}

interface RouterContextType {
  path: RoutePath;
  navigate: (newPath: RoutePath) => void;
}

const RouterContext = createContext<RouterContextType | undefined>(undefined);

export const RouterProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const getHashPath = useCallback((): RoutePath =>
    resolveInitialRoute(window.location.hash, !!localStorage.getItem('session_token')), []);

  const [path, setPath] = useState<RoutePath>(getHashPath);

  useEffect(() => {
    const handleHashChange = () => {
      setPath(getHashPath());
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, [getHashPath]);

  const navigate = useCallback((newPath: RoutePath) => {
    window.location.hash = newPath;
    setPath(newPath);
  }, []);

  const value = useMemo(() => ({ path, navigate }), [path, navigate]);

  return (
    <RouterContext.Provider value={value}>
      {children}
    </RouterContext.Provider>
  );
};

export const useRouter = () => {
  const context = useContext(RouterContext);
  if (!context) {
    throw new Error('useRouter must be used within a RouterProvider');
  }
  return context;
};

export const AppRouter: React.FC<{ user: { email: string; role: UserRole } }> = ({ user }) => {
  const { path, navigate } = useRouter();
  const effectivePath: AuthenticatedRoutePath = path === '/login' ? '/dashboard' : path;
  const allowedRoles = ROUTE_ROLES[effectivePath];
  const isAllowed = !allowedRoles || allowedRoles.includes(user.role);

  useEffect(() => {
    if (path === '/login' || !isAllowed) navigate('/dashboard');
  }, [isAllowed, navigate, path]);

  if (!isAllowed) return <AppLayout><DashboardPage /></AppLayout>;

  const Page = PAGE_COMPONENTS[effectivePath];

  return <AppLayout><Page /></AppLayout>;
};
