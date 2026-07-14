import React, { useEffect, useMemo, useState } from 'react';
import {
  TrendingUp, DollarSign, CreditCard,
  Percent, ArrowUpRight, ArrowDownRight, RefreshCw,
  FileText, UploadCloud, ShieldCheck,
} from 'lucide-react';
import { api } from '../../../api/client';
import { Button } from '../../../components/Button';
import { useCompany } from '../../companies/context/CompanyContext';
import type { Client, Site } from '../../../../shared/types';

type DashboardTransaction = {
  id: number;
  type: string;
  ref: string;
  account: string;
  amount: string;
  date: string;
  status: 'Posted' | 'Draft';
  siteCode: string;
  clientCode: string;
};

export const DashboardPage: React.FC = () => {
  const { activeCompany } = useCompany();
  const [sites, setSites] = useState<Site[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedSite, setSelectedSite] = useState('');
  const [selectedClient, setSelectedClient] = useState('');
  const [loadingScope, setLoadingScope] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadScopeOptions() {
      if (!activeCompany) {
        setSites([]);
        setClients([]);
        setSelectedSite('');
        setSelectedClient('');
        return;
      }

      setLoadingScope(true);
      try {
        const [siteRows, clientRows] = await Promise.all([
          api.get<Site[]>(`/sites?company_code=${encodeURIComponent(activeCompany.code)}`),
          api.get<Client[]>(`/clients?company_code=${encodeURIComponent(activeCompany.code)}`),
        ]);

        if (cancelled) return;
        setSites(siteRows);
        setClients(clientRows);
        setSelectedSite((current) => (
          current && siteRows.some((site) => site.site_code === current) ? current : ''
        ));
        setSelectedClient((current) => (
          current && clientRows.some((client) => client.client_code === current) ? current : ''
        ));
      } catch {
        if (!cancelled) {
          setSites([]);
          setClients([]);
          setSelectedSite('');
          setSelectedClient('');
        }
      } finally {
        if (!cancelled) setLoadingScope(false);
      }
    }

    void loadScopeOptions();
    return () => { cancelled = true; };
  }, [activeCompany?.code]);

  const stats = [
    {
      name: 'Total Revenue YTD',
      value: '$2,489,120.00',
      change: '+12.4%',
      isPositive: true,
      icon: DollarSign,
      color: 'text-emerald-500 bg-emerald-500/10',
    },
    {
      name: 'Total Expenses YTD',
      value: '$1,812,490.00',
      change: '+4.2%',
      isPositive: false,
      icon: CreditCard,
      color: 'text-rose-500 bg-rose-500/10',
    },
    {
      name: 'Gross Profit Margin',
      value: '52.3%',
      change: '+2.1%',
      isPositive: true,
      icon: Percent,
      color: 'text-indigo-500 bg-indigo-500/10',
    },
    {
      name: 'Net Profit YTD',
      value: '$676,630.00',
      change: '+28.7%',
      isPositive: true,
      icon: TrendingUp,
      color: 'text-purple-500 bg-purple-500/10',
    },
  ];

  const recentTransactions: DashboardTransaction[] = [
    { id: 1, type: 'Manual Journal', ref: 'JV-202607-04', account: 'Operating Revenue', amount: '+$45,000.00', date: 'Jul 12, 2026', status: 'Posted', siteCode: 'DEL', clientCode: 'CL-01' },
    { id: 2, type: 'CSV Import', ref: 'IMP-9874', account: 'Payroll Expense', amount: '-$12,300.00', date: 'Jul 10, 2026', status: 'Posted', siteCode: 'GGN', clientCode: 'CL-02' },
    { id: 3, type: 'Manual Journal', ref: 'JV-202607-03', account: 'Office Supplies', amount: '-$850.00', date: 'Jul 08, 2026', status: 'Draft', siteCode: 'DEL', clientCode: 'CL-01' },
    { id: 4, type: 'XLSX Import', ref: 'IMP-9860', account: 'Direct Material Cost', amount: '-$78,920.00', date: 'Jul 05, 2026', status: 'Posted', siteCode: 'GGN', clientCode: 'CL-03' },
  ];

  const visibleTransactions = useMemo(() => recentTransactions.filter((tx) => {
    if (selectedSite && tx.siteCode !== selectedSite) return false;
    if (selectedClient && tx.clientCode !== selectedClient) return false;
    return true;
  }), [recentTransactions, selectedClient, selectedSite]);

  const selectedSiteLabel = sites.find((site) => site.site_code === selectedSite)?.site_name || 'All sites';
  const selectedClientLabel = clients.find((client) => client.client_code === selectedClient)?.client_name || 'All clients';

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-slate-100">
            Financial Dashboard
          </h2>
          <p className="mt-1 text-slate-500 dark:text-slate-400">
            Real-time ledger overview for <span className="font-semibold text-indigo-500">{activeCompany?.name || 'All Companies'}</span>.
          </p>
          <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
            Scope: {selectedSiteLabel} · {selectedClientLabel}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="min-w-[180px]">
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-slate-400">Site</label>
            <select
              value={selectedSite}
              onChange={(event) => setSelectedSite(event.target.value)}
              disabled={!activeCompany || loadingScope}
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-semibold text-slate-800 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100"
            >
              <option value="">All sites</option>
              {sites.map((site) => (
                <option key={site.id} value={site.site_code}>
                  {site.site_name} ({site.site_code})
                </option>
              ))}
            </select>
          </div>

          <div className="min-w-[180px]">
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-slate-400">Client</label>
            <select
              value={selectedClient}
              onChange={(event) => setSelectedClient(event.target.value)}
              disabled={!activeCompany || loadingScope}
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-semibold text-slate-800 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100"
            >
              <option value="">All clients</option>
              {clients.map((client) => (
                <option key={client.id} value={client.client_code}>
                  {client.client_name} ({client.client_code})
                </option>
              ))}
            </select>
          </div>

          <button className="rounded-xl border border-slate-200 p-2.5 transition-all duration-150 hover:bg-slate-50 dark:border-slate-850 dark:hover:bg-slate-900">
            <RefreshCw className="h-4 w-4 text-slate-500 dark:text-slate-400" />
          </button>
          <Button variant="primary" leftIcon={<FileText className="h-4 w-4" />}>
            Generate Report
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, idx) => (
          <div
            key={idx}
            className="rounded-2xl border border-slate-200/50 bg-white p-6 shadow-md shadow-slate-100/50 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg dark:border-slate-850 dark:bg-slate-900/60 dark:shadow-none"
          >
            <div className="flex items-start justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                {stat.name}
              </span>
              <div className={`rounded-xl p-2.5 ${stat.color}`}>
                <stat.icon className="h-5 w-5" />
              </div>
            </div>

            <div className="mt-4">
              <h3 className="text-2xl font-black text-slate-800 dark:text-slate-100">
                {stat.value}
              </h3>
              <div className="mt-1 flex items-center space-x-1">
                {stat.isPositive ? (
                  <ArrowUpRight className="h-4 w-4 text-emerald-500" />
                ) : (
                  <ArrowDownRight className="h-4 w-4 text-rose-500" />
                )}
                <span className={`text-xs font-bold ${stat.isPositive ? 'text-emerald-500' : 'text-rose-500'}`}>
                  {stat.change}
                </span>
                <span className="text-xs text-slate-400 dark:text-slate-500">from last month</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <div className="rounded-2xl border border-slate-200/50 bg-white p-6 shadow-sm dark:border-slate-850 dark:bg-slate-900/60">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">
                Monthly Profit & Expense Trend
              </h3>
              <div className="flex items-center space-x-2 text-xs font-semibold text-slate-500">
                <span className="inline-block h-3 w-3 rounded-full bg-indigo-500" />
                <span>Revenue</span>
                <span className="ml-2 inline-block h-3 w-3 rounded-full bg-rose-500" />
                <span>Expenses</span>
              </div>
            </div>
            <div className="flex h-64 items-end justify-between border-b border-slate-100 px-4 pt-6 dark:border-slate-800">
              {[60, 45, 80, 50, 95, 70, 85, 90, 65, 75, 110, 100].map((h, i) => (
                <div key={i} className="flex w-full max-w-[24px] flex-col items-center space-y-2">
                  <div className="flex h-48 w-full items-end justify-center space-x-0.5">
                    <div className="w-2 rounded-t-sm bg-indigo-500" style={{ height: `${h}%` }} />
                    <div className="w-2 rounded-t-sm bg-rose-400" style={{ height: `${h * 0.7}%` }} />
                  </div>
                  <span className="font-mono text-[10px] text-slate-400">
                    {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][i]}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="space-y-4 rounded-2xl border border-slate-200/50 bg-white p-6 shadow-sm dark:border-slate-850 dark:bg-slate-900/60">
            <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">
              Direct Actions
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <button className="flex flex-col items-center justify-center rounded-xl border border-slate-150 bg-slate-50 p-4 transition-all hover:bg-indigo-500/5 hover:text-indigo-500 dark:border-slate-850 dark:bg-slate-900">
                <UploadCloud className="mb-2 h-6 w-6 text-slate-500 group-hover:text-indigo-500" />
                <span className="text-xs font-semibold">Bulk Upload</span>
              </button>
              <button className="flex flex-col items-center justify-center rounded-xl border border-slate-150 bg-slate-50 p-4 transition-all hover:bg-indigo-500/5 hover:text-indigo-500 dark:border-slate-850 dark:bg-slate-900">
                <FileText className="mb-2 h-6 w-6 text-slate-500 group-hover:text-indigo-500" />
                <span className="text-xs font-semibold">Manual Entry</span>
              </button>
            </div>
          </div>

          <div className="space-y-3 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 p-6 text-white shadow-lg shadow-indigo-500/10">
            <ShieldCheck className="h-8 w-8 text-indigo-100" />
            <h4 className="text-base font-bold">Ledger Integrity Active</h4>
            <p className="text-xs leading-relaxed text-indigo-100/90">
              D1 data sync has been verified. 0 ledger violations detected. Financial reporting is currently open for Jul 2026.
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200/50 bg-white p-6 shadow-sm dark:border-slate-850 dark:bg-slate-900/60">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">
            Recent Ledger Entries
          </h3>
          <button className="text-xs font-semibold text-indigo-500 hover:underline">
            View All History
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-100 text-left dark:divide-slate-800">
            <thead>
              <tr className="font-mono text-xs font-semibold text-slate-400">
                <th className="pb-3 pr-4">Type</th>
                <th className="px-4 pb-3">Reference</th>
                <th className="px-4 pb-3">Primary Account</th>
                <th className="px-4 pb-3">Site</th>
                <th className="px-4 pb-3">Client</th>
                <th className="px-4 pb-3">Date</th>
                <th className="px-4 pb-3 text-right">Amount</th>
                <th className="pb-3 pl-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50 text-sm dark:divide-slate-850">
              {visibleTransactions.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-sm text-slate-400">
                    No ledger entries match the selected site and client filters.
                  </td>
                </tr>
              ) : (
                visibleTransactions.map((tx) => (
                  <tr key={tx.id} className="text-slate-700 dark:text-slate-300">
                    <td className="py-3.5 pr-4 font-semibold">{tx.type}</td>
                    <td className="px-4 py-3.5 font-mono text-xs">{tx.ref}</td>
                    <td className="px-4 py-3.5 text-slate-500 dark:text-slate-400">{tx.account}</td>
                    <td className="px-4 py-3.5 text-slate-500 dark:text-slate-400">{tx.siteCode}</td>
                    <td className="px-4 py-3.5 text-slate-500 dark:text-slate-400">{tx.clientCode}</td>
                    <td className="px-4 py-3.5">{tx.date}</td>
                    <td className={`px-4 py-3.5 text-right font-mono font-semibold ${tx.amount.startsWith('+') ? 'text-emerald-500' : 'text-slate-700 dark:text-slate-300'}`}>
                      {tx.amount}
                    </td>
                    <td className="py-3.5 pl-4 text-right">
                      <span className={`inline-flex rounded-full px-2 py-0.5 text-2xs font-bold ${tx.status === 'Posted' ? 'bg-emerald-500/10 text-emerald-600' : 'bg-amber-500/10 text-amber-600'}`}>
                        {tx.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
