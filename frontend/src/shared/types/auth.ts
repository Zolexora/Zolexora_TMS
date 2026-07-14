export type UserRole = 'Admin' | 'FinanceAdmin' | 'Accountant' | 'DataEntry' | 'Viewer' | 'Auditor';

export interface UserSession {
  userId: string;
  email: string;
  name?: string | null;
  role: UserRole;
  exp: number;
  companyCodes: string[];
  identityProvider: 'cloudflare-access' | 'local-session' | 'test';
  allCompanyAccess?: boolean;
}
