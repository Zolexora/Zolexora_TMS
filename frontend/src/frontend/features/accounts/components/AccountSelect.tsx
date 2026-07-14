import React from 'react';
import type { AccountMaster } from '../../../../shared/types';

interface AccountSelectProps {
  accounts: AccountMaster[];
  value: string;
  onChange: (accountId: string) => void;
  includeInactive?: boolean;
  disabled?: boolean;
  label?: string;
}

/** Company-scoped account selector. Values are stable account IDs, never display names. */
export const AccountSelect: React.FC<AccountSelectProps> = ({
  accounts, value, onChange, includeInactive = false, disabled = false, label = 'Account',
}) => {
  const options = accounts.filter((account) => includeInactive || account.is_active);
  return (
    <label className="block text-sm font-semibold">
      {label}
      <select aria-label={label} value={value} onChange={(event) => onChange(event.target.value)} disabled={disabled}
        className="mt-1 w-full px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
        <option value="">Select an account</option>
        {options.map((account) => (
          <option key={account.id} value={account.id}>
            {account.code} — {account.name}{account.is_active ? '' : ' (Inactive)'}
          </option>
        ))}
      </select>
    </label>
  );
};
