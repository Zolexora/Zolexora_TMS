export * from './types';

import { AccountMaster, ImportValidationTemp } from './types';
export type Account = AccountMaster;
export type ImportValidation = ImportValidationTemp;

export function sanitizeXSS(str: string): string {
  if (!str) return str;
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#x27;");
}
