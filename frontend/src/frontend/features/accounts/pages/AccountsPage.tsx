import React, { useState, useEffect } from 'react';
import { useCompany } from '../../companies/context/CompanyContext';
import { useAuth } from '../../auth/hooks/useAuth';
import { api } from '../../../api/client';
import { AccountMaster, PLGroup } from '../../../../shared/types';
import { Plus, Edit2, ShieldAlert, X, AlertCircle, Coins, Eye } from 'lucide-react';
import { PERMISSIONS } from '../../../../shared/permissions';

export function formatMinorUnits(valueInMinorUnits: number, currencyCode: string = 'INR'): string {
  const amount = valueInMinorUnits / 100;
  const localeMap: Record<string, string> = {
    INR: 'en-IN',
    USD: 'en-US',
    EUR: 'de-DE',
    GBP: 'en-GB',
  };
  const locale = localeMap[currencyCode] || 'en-US';
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currencyCode,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

// Extends AccountMaster model with balance field from api
interface AccountWithBalance extends AccountMaster {
  balance?: number;
}

export const AccountsPage: React.FC = () => {
  const { activeCompany } = useCompany();
  const { can } = useAuth();
  const canManage = can(PERMISSIONS.ACCOUNT_MANAGE);

  const [accounts, setAccounts] = useState<AccountWithBalance[]>([]);
  const [groups, setGroups] = useState<PLGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Modal / Form state
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState<AccountWithBalance | null>(null);
  const [viewingAccount, setViewingAccount] = useState<AccountWithBalance | null>(null);

  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [plGroupId, setPlGroupId] = useState<string>('');
  const [decimalBalance, setDecimalBalance] = useState<string>('0.00');
  const [search, setSearch] = useState('');
  const [activeFilter, setActiveFilter] = useState<'all' | 'true' | 'false'>('all');

  const fetchAccountsAndGroups = async () => {
    if (!activeCompany) return;
    setLoading(true);
    setError(null);
    try {
      const [accountsData, groupsData] = await Promise.all([
        api.get<AccountWithBalance[]>(`/accounts?company_code=${encodeURIComponent(activeCompany.code)}&search=${encodeURIComponent(search)}&is_active=${activeFilter}`),
        api.get<PLGroup[]>(`/pl-groups?company_code=${encodeURIComponent(activeCompany.code)}`),
      ]);
      setAccounts(accountsData || []);
      setGroups(groupsData || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load chart of accounts data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccountsAndGroups();
  }, [activeCompany, search, activeFilter]);

  const resetForm = () => {
    setCode('');
    setName('');
    setPlGroupId('');
    setDecimalBalance('0.00');
    setError(null);
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCompany) return;
    if (!code.trim()) {
      setError('Account code is required.');
      return;
    }
    if (!name.trim()) {
      setError('Account name is required.');
      return;
    }

    // Convert decimal balance to minor units integer
    const parsedBal = parseFloat(decimalBalance);
    const balanceInMinor = isNaN(parsedBal) ? 0 : Math.round((parsedBal + (parsedBal >= 0 ? Number.EPSILON : -Number.EPSILON)) * 100);

    try {
      setError(null);
      await api.post('/accounts', {
        code: code.trim(),
        company_code: activeCompany.code,
        name: name.trim(),
        pl_group_id: plGroupId ? plGroupId : null,
        balance: balanceInMinor,
      });
      await fetchAccountsAndGroups();
      setIsAddOpen(false);
      resetForm();
    } catch (err: any) {
      setError(err.message || 'Failed to create account.');
    }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCompany || !editingAccount) return;
    if (!code.trim()) {
      setError('Account code is required.');
      return;
    }
    if (!name.trim()) {
      setError('Account name is required.');
      return;
    }

    try {
      setError(null);
      await api.patch(`/accounts/${editingAccount.id}?company_code=${encodeURIComponent(activeCompany.code)}`, {
        name: name.trim(),
        pl_group_id: plGroupId ? plGroupId : null,
      });
      await fetchAccountsAndGroups();
      setEditingAccount(null);
      resetForm();
    } catch (err: any) {
      setError(err.message || 'Failed to update account.');
    }
  };

  const toggleActive = async (account: AccountWithBalance) => {
    if (!activeCompany) return;
    try {
      setError(null);
      await api.patch(`/accounts/${account.id}?company_code=${encodeURIComponent(activeCompany.code)}`, { is_active: !account.is_active });
      await fetchAccountsAndGroups();
    } catch (err: any) {
      setError(err.message || 'Failed to change account status.');
    }
  };

  const getGroupName = (id: any) => {
    if (!id) return '[No P&L Group]';
    const grp = groups.find(g => String(g.id) === String(id));
    return grp ? grp.name : `[Group ID: ${id}]`;
  };

  if (!activeCompany) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl">
        <ShieldAlert className="h-12 w-12 text-amber-500 mb-4" />
        <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">No Active Company Selected</h3>
        <p className="text-slate-500 dark:text-slate-400 mt-1 max-w-sm text-center">
          Please select a company from the header dropdown to view the chart of accounts.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center space-y-4 sm:space-y-0">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-800 dark:text-slate-100">
            Chart of Accounts — {activeCompany.name}
          </h2>
          <p className="text-slate-500 dark:text-slate-400">
            Manage general ledger accounts, mapping to P&L Groups, and view active ledger balances.
          </p>
        </div>

        {canManage && (
          <button
            onClick={() => {
              resetForm();
              setIsAddOpen(true);
            }}
            className="flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-xl transition-all shadow-md shadow-indigo-500/10 self-start sm:self-auto font-medium"
          >
            <Plus className="h-4 w-4" />
            <span>Add Account</span>
          </button>
        )}
      </div>

      <div className="flex flex-col sm:flex-row gap-3 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4">
        <input aria-label="Search accounts" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search account code or name"
          className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950" />
        <select aria-label="Filter account status" value={activeFilter} onChange={(e) => setActiveFilter(e.target.value as 'all' | 'true' | 'false')}
          className="px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950">
          <option value="all">All accounts</option><option value="true">Active</option><option value="false">Inactive</option>
        </select>
      </div>

      <div className="bg-white dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-850 backdrop-blur-md rounded-2xl shadow-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
            <thead className="bg-slate-50 dark:bg-slate-950/50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Account Code</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Account Name</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">P&L Group Category</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Active Balance</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {loading && accounts.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-slate-400 dark:text-slate-500">
                    Loading accounts...
                  </td>
                </tr>
              ) : accounts.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-400 dark:text-slate-500">
                    No accounts created for this company. Click "Add Account" to configure one.
                  </td>
                </tr>
              ) : (
                accounts.map((acc) => (
                  <tr key={acc.code} className="hover:bg-slate-50/50 dark:hover:bg-slate-850/20 transition-colors">
                    <td className="px-6 py-4 font-mono text-sm text-indigo-600 dark:text-indigo-400 font-semibold">{acc.code}</td>
                    <td className="px-6 py-4 text-sm font-semibold text-slate-800 dark:text-slate-200">{acc.name}</td>
                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">{getGroupName(acc.pl_group_id)}</td>
                    <td className="px-6 py-4 text-right text-sm font-mono font-semibold text-slate-800 dark:text-slate-200">
                      {formatMinorUnits(acc.balance || 0, activeCompany.currency)}
                    </td>
                    <td className="px-6 py-4"><span className={`px-2 py-1 rounded-full text-xs font-semibold ${acc.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-600'}`}>{acc.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td className="px-6 py-4 text-right text-sm space-x-2">
                      <button
                        onClick={() => {
                          setViewingAccount(acc);
                        }}
                        className="p-1.5 text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-indigo-500/10 rounded-lg transition-colors inline-flex items-center space-x-1"
                      >
                        <Eye className="h-4 w-4" />
                        <span>View</span>
                      </button>

                      {canManage && (
                        <>
                        <button
                          onClick={() => {
                            setEditingAccount(acc);
                            setCode(acc.code);
                            setName(acc.name);
                            setPlGroupId(acc.pl_group_id ? String(acc.pl_group_id) : '');
                            setDecimalBalance(((acc.balance || 0) / 100).toFixed(2));
                            setError(null);
                          }}
                          className="p-1.5 text-slate-500 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-indigo-500/10 rounded-lg transition-colors inline-flex items-center space-x-1"
                        >
                          <Edit2 className="h-4 w-4" />
                          <span>Edit</span>
                        </button>
                        <button onClick={() => void toggleActive(acc)} className="p-1.5 text-amber-600 hover:bg-amber-500/10 rounded-lg">
                          {acc.is_active ? 'Deactivate' : 'Reactivate'}
                        </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Account Modal */}
      {isAddOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden">
            <div className="flex justify-between items-center px-6 py-4 border-b border-slate-200 dark:border-slate-800">
              <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">Add Account</h3>
              <button onClick={() => setIsAddOpen(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleAdd} className="p-6 space-y-4">
              {error && (
                <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 text-sm flex items-start space-x-2">
                  <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Account Code
                </label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="e.g. 1001-cash"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Account Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Cash in Hand"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  P&L Group Mapping
                </label>
                <select
                  value={plGroupId}
                  onChange={(e) => setPlGroupId(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="">[None — Unmapped]</option>
                  {groups.map(g => (
                    <option key={g.id} value={g.id}>
                      {g.name} ({g.id}) — {g.normal_direction === 'credit' ? 'Revenue' : 'Expense'}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Initial Balance ({activeCompany.currency})
                </label>
                <div className="relative">
                  <input
                    type="number"
                    step="0.01"
                    value={decimalBalance}
                    onChange={(e) => setDecimalBalance(e.target.value)}
                    placeholder="0.00"
                    className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 font-mono focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                  <Coins className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-400" />
                </div>
                <p className="text-2xs text-slate-400">Values are converted and stored as minor units integers (paise).</p>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAddOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-550 text-white text-sm font-medium shadow-lg shadow-indigo-500/10"
                >
                  Create Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Account Modal */}
      {editingAccount && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden">
            <div className="flex justify-between items-center px-6 py-4 border-b border-slate-200 dark:border-slate-800">
              <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">Edit Account: {editingAccount.code}</h3>
              <button onClick={() => setEditingAccount(null)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleEdit} className="p-6 space-y-4">
              {error && (
                <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 text-sm flex items-start space-x-2">
                  <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Account Code
                </label>
                <input
                  type="text"
                  value={code}
                  disabled
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-500"
                />
                <p className="text-2xs text-slate-400">Account codes are stable identifiers and cannot be renamed.</p>
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Account Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Cash in Hand"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  P&L Group Mapping
                </label>
                <select
                  value={plGroupId}
                  onChange={(e) => setPlGroupId(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="">[None — Unmapped]</option>
                  {groups.map(g => (
                    <option key={g.id} value={g.id}>
                      {g.name} ({g.id}) — {g.normal_direction === 'credit' ? 'Revenue' : 'Expense'}
                    </option>
                  ))}
                </select>
              </div>

              <p className="text-xs text-amber-600 dark:text-amber-400">Posted balances are immutable. Correct financial history with a reversal or adjustment workflow.</p>

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setEditingAccount(null)}
                  className="px-4 py-2 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-550 text-white text-sm font-medium shadow-lg shadow-indigo-500/10"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Account Modal */}
      {viewingAccount && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden">
            <div className="flex justify-between items-center px-6 py-4 border-b border-slate-200 dark:border-slate-800">
              <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">Account Details</h3>
              <button onClick={() => setViewingAccount(null)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="block text-2xs uppercase tracking-wider text-slate-400">Account Code</span>
                  <span className="font-mono text-sm font-bold text-slate-800 dark:text-slate-200">{viewingAccount.code}</span>
                </div>
                <div>
                  <span className="block text-2xs uppercase tracking-wider text-slate-400">Account Name</span>
                  <span className="text-sm font-bold text-slate-800 dark:text-slate-200">{viewingAccount.name}</span>
                </div>
                <div>
                  <span className="block text-2xs uppercase tracking-wider text-slate-400">P&L Group Scope</span>
                  <span className="text-sm font-semibold text-slate-600 dark:text-slate-400">{getGroupName(viewingAccount.pl_group_id)}</span>
                </div>
                <div>
                  <span className="block text-2xs uppercase tracking-wider text-slate-400">Active Balance</span>
                  <span className="text-sm font-mono font-bold text-slate-800 dark:text-slate-200">
                    {formatMinorUnits(viewingAccount.balance || 0, activeCompany.currency)}
                  </span>
                </div>
              </div>

              <div className="flex justify-end pt-4 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setViewingAccount(null)}
                  className="px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-850 hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 text-sm font-medium transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
