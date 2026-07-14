import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, CheckCircle, Copy, Plus, Save, Send, Trash2 } from 'lucide-react';
import { api } from '../../../api/client';
import { Button } from '../../../components/Button';
import { Input } from '../../../components/Input';
import { useCompany } from '../../companies/context/CompanyContext';
import type { AccountMaster } from '../../../../shared/types';

interface EntryRow {
  id: string;
  accountCode: string;
  direction: 'Debit' | 'Credit';
  amount: string;
  remarks: string;
}

interface Notice {
  kind: 'success' | 'error';
  message: string;
}

function batchIdFromReference(reference: string): string {
  const trimmed = reference.trim();
  if (!trimmed) return `batch-${Date.now()}`;
  return trimmed.replace(/[^A-Za-z0-9_-]+/g, '-');
}

function amountToNumber(value: string): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export const ManualEntryPage: React.FC = () => {
  const { activeCompany } = useCompany();
  const [entryDate, setEntryDate] = useState(new Date().toISOString().slice(0, 10));
  const [reference, setReference] = useState('');
  const [description, setDescription] = useState('');
  const [rows, setRows] = useState<EntryRow[]>([
    { id: crypto.randomUUID(), accountCode: '', direction: 'Debit', amount: '', remarks: '' },
    { id: crypto.randomUUID(), accountCode: '', direction: 'Credit', amount: '', remarks: '' },
  ]);
  const [siteCode, setSiteCode] = useState('');
  const [clientCode, setClientCode] = useState('');
  const [vehicleRegNo, setVehicleRegNo] = useState('');
  const [managerCode, setManagerCode] = useState('');
  const [accounts, setAccounts] = useState<AccountMaster[]>([]);
  const [loadingAccounts, setLoadingAccounts] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const businessType = activeCompany?.business_type?.trim().toLowerCase() ?? '';
  const requiresSite = useMemo(() => (
    businessType.includes('transport') || businessType.includes('hotel') || businessType.includes('dairy')
  ), [businessType]);
  const requiresTransport = useMemo(() => businessType.includes('transport'), [businessType]);

  useEffect(() => {
    let cancelled = false;
    async function loadAccounts() {
      if (!activeCompany) {
        setAccounts([]);
        return;
      }
      setLoadingAccounts(true);
      try {
        const data = await api.get<AccountMaster[]>(`/accounts?company_code=${encodeURIComponent(activeCompany.code)}&is_active=true`);
        if (!cancelled) setAccounts(data);
      } catch (error) {
        if (!cancelled) {
          setAccounts([]);
          setNotice({ kind: 'error', message: error instanceof Error ? error.message : 'Failed to load accounts.' });
        }
      } finally {
        if (!cancelled) setLoadingAccounts(false);
      }
    }

    void loadAccounts();
    return () => { cancelled = true; };
  }, [activeCompany?.code]);

  const debitTotal = rows.reduce((sum, row) => sum + (row.direction === 'Debit' ? amountToNumber(row.amount) : 0), 0);
  const creditTotal = rows.reduce((sum, row) => sum + (row.direction === 'Credit' ? amountToNumber(row.amount) : 0), 0);
  const isBalanced = debitTotal > 0 && debitTotal === creditTotal;

  const transportFieldsMissing = requiresTransport
    ? [
      !siteCode.trim() ? 'Site code' : '',
      !clientCode.trim() ? 'Client code' : '',
      !vehicleRegNo.trim() ? 'Vehicle registration number' : '',
      !managerCode.trim() ? 'Manager code' : '',
    ].filter(Boolean)
    : [];

  const resetDraft = () => {
    setReference('');
    setDescription('');
    setRows([
      { id: crypto.randomUUID(), accountCode: '', direction: 'Debit', amount: '', remarks: '' },
      { id: crypto.randomUUID(), accountCode: '', direction: 'Credit', amount: '', remarks: '' },
    ]);
    setSiteCode('');
    setClientCode('');
    setVehicleRegNo('');
    setManagerCode('');
  };

  const validate = () => {
    if (!activeCompany) {
      setFormError('Select a company first.');
      return false;
    }
    if (rows.length < 2) {
      setFormError('Add at least two ledger lines.');
      return false;
    }
    if (!isBalanced) {
      setFormError('Debits and credits must balance before saving or posting.');
      return false;
    }
    if (requiresSite && !siteCode.trim()) {
      setFormError('Site is required for this company.');
      return false;
    }
    if (requiresTransport && transportFieldsMissing.length) {
      setFormError(`Missing transport dimensions: ${transportFieldsMissing.join(', ')}.`);
      return false;
    }
    for (const [index, row] of rows.entries()) {
      if (!row.accountCode.trim()) {
        setFormError(`Select an account on line ${index + 1}.`);
        return false;
      }
      if (!Number.isFinite(Number(row.amount)) || Number(row.amount) < 0) {
        setFormError(`Line ${index + 1} amount must be a non-negative number.`);
        return false;
      }
    }
    return true;
  };

  const buildPayload = () => ({
    id: batchIdFromReference(reference),
    company_code: activeCompany?.code,
    created_at: `${entryDate}T00:00:00.000Z`,
    reference: reference.trim() || null,
    description: description.trim() || null,
    batch_type: 'standard',
    site_code: siteCode.trim() || null,
    client_code: clientCode.trim() || null,
    vehicle_reg_no: vehicleRegNo.trim() || null,
    manager_code: managerCode.trim() || null,
    entries: rows.map((row) => ({
      account_code: row.accountCode,
      debit: row.direction === 'Debit' ? amountToNumber(row.amount) : 0,
      credit: row.direction === 'Credit' ? amountToNumber(row.amount) : 0,
      description: row.remarks.trim() || null,
    })),
  });

  const submit = async (postImmediately: boolean) => {
    if (!validate()) return;
    setSaving(true);
    setNotice(null);
    setFormError(null);
    const payload = buildPayload();
    try {
      await api.post('/entries', payload);
      if (postImmediately) {
        await api.post(`/entries/${payload.id}/post`, {});
      }
      setNotice({
        kind: 'success',
        message: postImmediately ? 'Entry batch saved and posted.' : 'Draft entry batch saved.',
      });
      resetDraft();
    } catch (error) {
      setNotice(null);
      setFormError(error instanceof Error ? error.message : 'Failed to save entry batch.');
    } finally {
      setSaving(false);
    }
  };

  const updateRow = (id: string, field: keyof EntryRow, value: string) => {
    setRows((current) => current.map((row) => (row.id === id ? { ...row, [field]: value } : row)));
  };

  const duplicateRow = (row: EntryRow) => {
    setRows((current) => [...current, { ...row, id: crypto.randomUUID() }]);
  };

  const removeRow = (id: string) => {
    setRows((current) => (current.length > 2 ? current.filter((row) => row.id !== id) : current));
  };

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="space-y-1">
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-slate-100">Manual Entry</h2>
          <p className="text-slate-500 dark:text-slate-400">
            Create a monthly journal batch for <span className="font-semibold text-indigo-500">{activeCompany?.name || 'the selected company'}</span>.
          </p>
          {requiresTransport && (
            <p className="text-xs font-semibold text-amber-600 dark:text-amber-400">
              Transport companies require Site, Client, Vehicle, and Manager on every batch.
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-3">
          <Button variant="outline" leftIcon={<Save className="h-4 w-4" />} isLoading={saving} onClick={() => void submit(false)}>
            Save Draft
          </Button>
          <Button leftIcon={<Send className="h-4 w-4" />} isLoading={saving} onClick={() => void submit(true)} disabled={!isBalanced}>
            Post Entry
          </Button>
        </div>
      </div>

      {notice && (
        <div className={`rounded-2xl border px-4 py-3 text-sm ${
          notice.kind === 'success'
            ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400'
            : 'border-red-500/20 bg-red-500/10 text-red-700 dark:text-red-400'
        }`}>
          <div className="flex items-center gap-3">
            <CheckCircle className="h-4 w-4 shrink-0" />
            <span className="flex-1">{notice.message}</span>
            <button className="text-current underline" onClick={() => setNotice(null)}>Dismiss</button>
          </div>
        </div>
      )}

      {formError && (
        <div className="rounded-2xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-700 dark:text-red-400">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{formError}</span>
          </div>
        </div>
      )}

      <div className="grid gap-4 rounded-2xl border border-slate-200/70 bg-white p-5 shadow-sm dark:border-slate-800/70 dark:bg-slate-900/60 md:grid-cols-3">
        <Input label="Entry Date" type="date" value={entryDate} onChange={(e) => setEntryDate(e.target.value)} />
        <Input label="Reference" placeholder="Optional batch reference" value={reference} onChange={(e) => setReference(e.target.value)} />
        <Input label="Description" placeholder="Batch description" value={description} onChange={(e) => setDescription(e.target.value)} />
      </div>

      <div className="rounded-2xl border border-slate-200/70 bg-white p-5 shadow-sm dark:border-slate-800/70 dark:bg-slate-900/60">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">Company Dimensions</h3>
            <p className="text-xs text-slate-500">
              {requiresSite ? 'Site is required.' : 'Optional for the current company type.'}
            </p>
          </div>
          <div className="text-xs font-mono text-slate-400">
            {loadingAccounts ? 'Loading accounts…' : `${accounts.length} accounts loaded`}
          </div>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <Input
            label="Site code"
            placeholder={requiresSite ? 'Required' : 'Optional'}
            value={siteCode}
            onChange={(e) => setSiteCode(e.target.value)}
          />
          <Input
            label="Client code"
            placeholder={requiresTransport ? 'Required for transport' : 'Optional'}
            value={clientCode}
            onChange={(e) => setClientCode(e.target.value)}
          />
          <Input
            label="Vehicle registration number"
            placeholder={requiresTransport ? 'Required for transport' : 'Optional'}
            value={vehicleRegNo}
            onChange={(e) => setVehicleRegNo(e.target.value)}
          />
          <Input
            label="Manager code"
            placeholder={requiresTransport ? 'Required for transport' : 'Optional'}
            value={managerCode}
            onChange={(e) => setManagerCode(e.target.value)}
          />
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200/70 bg-white p-5 shadow-sm dark:border-slate-800/70 dark:bg-slate-900/60">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">Ledger Lines</h3>
            <p className="text-xs text-slate-500">Use account codes already configured for the selected company.</p>
          </div>
          <Button variant="outline" size="sm" leftIcon={<Plus className="h-4 w-4" />} onClick={() => setRows((current) => [...current, { id: crypto.randomUUID(), accountCode: '', direction: 'Debit', amount: '', remarks: '' }])}>
            Add Line
          </Button>
        </div>

        <div className="mt-4 overflow-x-auto rounded-xl border border-slate-100 dark:border-slate-800">
          <table className="min-w-full divide-y divide-slate-100 text-left dark:divide-slate-800">
            <thead className="bg-slate-50 dark:bg-slate-950/50">
              <tr className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                <th className="w-14 px-4 py-3 text-center">#</th>
                <th className="min-w-[220px] px-4 py-3">Account</th>
                <th className="w-40 px-4 py-3">Direction</th>
                <th className="w-44 px-4 py-3 text-right">Amount</th>
                <th className="min-w-[220px] px-4 py-3">Remarks</th>
                <th className="w-24 px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50 dark:divide-slate-850">
              {rows.map((row, index) => (
                <tr key={row.id} className="align-top">
                  <td className="px-4 py-3 text-center text-sm text-slate-400">{index + 1}</td>
                  <td className="px-4 py-3">
                    <select
                      value={row.accountCode}
                      onChange={(e) => updateRow(row.id, 'accountCode', e.target.value)}
                      className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm dark:border-slate-800 dark:bg-slate-950"
                    >
                      <option value="">Select account</option>
                      {accounts.map((account) => (
                        <option key={account.id} value={account.code}>
                          {account.code} - {account.name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <select
                      value={row.direction}
                      onChange={(e) => updateRow(row.id, 'direction', e.target.value as EntryRow['direction'])}
                      className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm dark:border-slate-800 dark:bg-slate-950"
                    >
                      <option value="Debit">Debit</option>
                      <option value="Credit">Credit</option>
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <Input
                      type="number"
                      min="0"
                      step="1"
                      value={row.amount}
                      onChange={(e) => updateRow(row.id, 'amount', e.target.value)}
                      className="text-right font-mono"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <Input
                      placeholder="Optional row note"
                      value={row.remarks}
                      onChange={(e) => updateRow(row.id, 'remarks', e.target.value)}
                    />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      <Button type="button" variant="ghost" size="sm" onClick={() => duplicateRow(row)} leftIcon={<Copy className="h-4 w-4" />}>
                        Copy
                      </Button>
                      <Button type="button" variant="ghost" size="sm" onClick={() => removeRow(row.id)} leftIcon={<Trash2 className="h-4 w-4" />}>
                        Remove
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 flex flex-col gap-2 rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600 dark:bg-slate-950/50 dark:text-slate-400 md:flex-row md:items-center md:justify-between">
          <span>Debit total: <span className="font-mono font-semibold">{debitTotal.toLocaleString()}</span></span>
          <span>Credit total: <span className="font-mono font-semibold">{creditTotal.toLocaleString()}</span></span>
          <span className={isBalanced ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}>
            {isBalanced ? 'Balanced' : 'Not balanced'}
          </span>
        </div>
      </div>
    </div>
  );
};
