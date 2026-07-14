import type { UserRole } from './types';

export const PERMISSIONS = {
  COMPANY_MANAGE: 'company:manage',
  PL_GROUP_MANAGE: 'pl-group:manage',
  ACCOUNT_MANAGE: 'account:manage',
  ENTRY_CREATE: 'entry:create',
  ENTRY_POST: 'entry:post',
  ENTRY_REVERSE: 'entry:reverse',
  IMPORT_VALIDATE: 'import:validate',
  IMPORT_CONFIRM: 'import:confirm',
  PERIOD_LOCK: 'period:lock',
  PERIOD_UNLOCK: 'period:unlock',
  PERIOD_CLOSE: 'period:close',
  PERIOD_REOPEN: 'period:reopen',
  FINANCIAL_YEAR_MANAGE: 'financial-year:manage',
} as const;

export type Permission = typeof PERMISSIONS[keyof typeof PERMISSIONS];

const allPermissions = Object.values(PERMISSIONS);
export const ROLE_PERMISSIONS: Record<UserRole, readonly Permission[]> = {
  Admin: allPermissions,
  FinanceAdmin: allPermissions.filter((permission) => permission !== PERMISSIONS.COMPANY_MANAGE),
  Accountant: [
    PERMISSIONS.ACCOUNT_MANAGE,
    PERMISSIONS.ENTRY_CREATE,
    PERMISSIONS.ENTRY_POST,
    PERMISSIONS.ENTRY_REVERSE,
    PERMISSIONS.IMPORT_VALIDATE,
    PERMISSIONS.IMPORT_CONFIRM,
  ],
  DataEntry: [PERMISSIONS.ENTRY_CREATE, PERMISSIONS.IMPORT_VALIDATE],
  Viewer: [],
  Auditor: [],
};

export function roleHasPermission(role: UserRole, permission: Permission): boolean {
  return ROLE_PERMISSIONS[role].includes(permission);
}
