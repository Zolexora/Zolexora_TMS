import React, { useState } from 'react';
import { AlertCircle, CalendarRange, Lock, Plus, RefreshCw, ShieldAlert, Unlock, X } from 'lucide-react';
import type { FinancialPeriod } from '../../../../shared/types';
import { PERMISSIONS } from '../../../../shared/permissions';
import { api } from '../../../api/client';
import { useAuth } from '../../auth/hooks/useAuth';
import { useCompany } from '../../companies/context/CompanyContext';
import { usePeriod } from '../context/PeriodContext';

function message(error: unknown): string {
  return error instanceof Error ? error.message : 'The period operation failed.';
}

function statusClass(status: FinancialPeriod['status']): string {
  if (status === 'open') return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400';
  if (status === 'closed') return 'bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400';
  return 'bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-400';
}

export const PeriodsPage: React.FC = () => {
  const { activeCompany } = useCompany();
  const { can } = useAuth();
  const {
    years, periods, activeYear, loading, setActiveYear, refreshYears, refreshPeriods,
  } = usePeriod();
  const [createOpen, setCreateOpen] = useState(false);
  const [name, setName] = useState('2026-27');
  const [startDate, setStartDate] = useState('2026-04-01');
  const [endDate, setEndDate] = useState('2027-03-31');
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createYear = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!activeCompany) return;
    setWorking(true); setError(null);
    try {
      await api.post('/financial-years', {
        company_code: activeCompany.code, name, start_date: startDate, end_date: endDate,
      });
      await refreshYears();
      setCreateOpen(false);
    } catch (caught) {
      setError(message(caught));
    } finally {
      setWorking(false);
    }
  };

  const transition = async (period: FinancialPeriod, action: 'close' | 'reopen' | 'lock' | 'unlock') => {
    if (!window.confirm(`${action[0].toUpperCase()}${action.slice(1)} period ${period.period_code}?`)) return;
    setWorking(true); setError(null);
    try {
      await api.post(`/financial-periods/${period.id}/${action}`, { reason: `Changed from period manager` });
      await refreshPeriods();
    } catch (caught) {
      setError(message(caught));
    } finally {
      setWorking(false);
    }
  };

  const deactivateYear = async () => {
    if (!activeYear || !window.confirm(`Deactivate financial year ${activeYear.name}? Historical data remains available.`)) return;
    setWorking(true); setError(null);
    try {
      await api.delete(`/financial-years/${activeYear.id}`);
      await refreshYears();
    } catch (caught) {
      setError(message(caught));
    } finally {
      setWorking(false);
    }
  };

  if (!activeCompany) {
    return (
      <div className="flex flex-col items-center justify-center py-12 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
        <ShieldAlert className="h-12 w-12 text-amber-500 mb-4" />
        <h2 className="text-lg font-bold">Select a company to manage financial periods</h2>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Financial Years & Periods</h2>
          <p className="text-slate-500 dark:text-slate-400">{activeCompany.name} · D1-authoritative reporting calendar</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select
            aria-label="Manage financial year"
            value={activeYear?.id || ''}
            onChange={(event) => setActiveYear(years.find((year) => year.id === event.target.value) || null)}
            className="px-4 py-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 font-semibold"
          >
            <option value="">Select financial year</option>
            {years.map((year) => <option key={year.id} value={year.id}>{year.name}{year.is_active ? '' : ' (Inactive)'}</option>)}
          </select>
          <button
            onClick={() => { void refreshYears(); void refreshPeriods(); }}
            disabled={loading || working}
            aria-label="Refresh financial periods"
            className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800"
          ><RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /></button>
          {can(PERMISSIONS.FINANCIAL_YEAR_MANAGE) && (
            <button onClick={() => setCreateOpen(true)} className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 text-white font-semibold">
              <Plus className="h-4 w-4" /> New Year
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 flex gap-2">
          <AlertCircle className="h-5 w-5 flex-shrink-0" /><span>{error}</span>
        </div>
      )}

      {activeYear && (
        <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <div>
            <p className="font-bold text-slate-800 dark:text-slate-100">{activeYear.name}</p>
            <p className="text-sm text-slate-500">{activeYear.start_date} through {activeYear.end_date}</p>
          </div>
          {can(PERMISSIONS.FINANCIAL_YEAR_MANAGE) && activeYear.is_active && (
            <button onClick={deactivateYear} className="text-sm font-semibold text-red-600 hover:text-red-700">Deactivate year</button>
          )}
        </div>
      )}

      {!activeYear ? (
        <div className="py-16 text-center rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 text-slate-500">
          No financial year exists for this company. Create one to generate twelve monthly periods.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {periods.map((period) => (
            <article key={period.id} className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-mono text-xs text-slate-500">{period.period_code}</p>
                  <h3 className="font-bold flex items-center gap-2"><CalendarRange className="h-4 w-4 text-indigo-500" />{period.start_date}</h3>
                  <p className="text-xs text-slate-400">through {period.end_date}</p>
                </div>
                <span className={`px-2.5 py-1 rounded-full text-2xs uppercase font-bold ${statusClass(period.status)}`}>{period.status}</span>
              </div>
              <div className="flex flex-wrap gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
                {period.status === 'open' && can(PERMISSIONS.PERIOD_CLOSE) && (
                  <button onClick={() => transition(period, 'close')} disabled={working} className="px-3 py-1.5 rounded-lg bg-amber-500/10 text-amber-700 text-xs font-semibold">Close</button>
                )}
                {period.status === 'closed' && can(PERMISSIONS.PERIOD_REOPEN) && (
                  <button onClick={() => transition(period, 'reopen')} disabled={working} className="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-700 text-xs font-semibold"><Unlock className="inline h-3 w-3 mr-1" />Reopen</button>
                )}
                {period.status !== 'locked' && can(PERMISSIONS.PERIOD_LOCK) && (
                  <button onClick={() => transition(period, 'lock')} disabled={working} className="px-3 py-1.5 rounded-lg bg-red-500/10 text-red-700 text-xs font-semibold"><Lock className="inline h-3 w-3 mr-1" />Lock</button>
                )}
                {period.status === 'locked' && can(PERMISSIONS.PERIOD_UNLOCK) && (
                  <button onClick={() => transition(period, 'unlock')} disabled={working} className="px-3 py-1.5 rounded-lg bg-slate-500/10 text-slate-700 dark:text-slate-300 text-xs font-semibold">Unlock</button>
                )}
              </div>
            </article>
          ))}
        </div>
      )}

      {createOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl">
            <div className="flex items-center justify-between p-5 border-b border-slate-200 dark:border-slate-800">
              <h3 className="text-lg font-bold">Create financial year</h3>
              <button onClick={() => setCreateOpen(false)} aria-label="Close financial year form"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={createYear} className="p-5 space-y-4">
              <label className="block text-sm font-semibold">Name
                <input value={name} onChange={(event) => setName(event.target.value)} className="mt-1 w-full px-3 py-2 rounded-xl border dark:bg-slate-950 dark:border-slate-800" required />
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <label className="block text-sm font-semibold">Start date
                  <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} className="mt-1 w-full px-3 py-2 rounded-xl border dark:bg-slate-950 dark:border-slate-800" required />
                </label>
                <label className="block text-sm font-semibold">End date
                  <input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} className="mt-1 w-full px-3 py-2 rounded-xl border dark:bg-slate-950 dark:border-slate-800" required />
                </label>
              </div>
              <p className="text-xs text-slate-500">A financial year starts on day 01 and spans exactly twelve calendar months. Twelve open periods are generated atomically.</p>
              <button disabled={working} className="w-full py-2.5 rounded-xl bg-indigo-600 text-white font-semibold disabled:opacity-50">{working ? 'Creating…' : 'Create year and periods'}</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
