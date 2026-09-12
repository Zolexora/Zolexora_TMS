import { useQuery } from '@tanstack/react-query';
import { IndianRupee, TrendingUp, TrendingDown, Activity, AlertCircle } from 'lucide-react';
import { apiClient } from '../../lib/api';

export function PnLReportsPage() {
  const { data: plSummary, isLoading } = useQuery({
    queryKey: ['pl-summary'],
    queryFn: () => apiClient<any>('/api/v1/pl/summary')
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Profit & Loss Dashboard</h1>
          <p className="text-sm text-slate-400">Live operational financial summary from invoices, payables, and expenses.</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12">
          <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-t-2 border-indigo-500"></div>
        </div>
      ) : !plSummary ? (
        <div className="flex justify-center p-12 text-slate-400">Failed to load P&L summary.</div>
      ) : (
        <div className="grid gap-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
              <div className="flex items-center gap-2 text-sm font-medium text-emerald-400 mb-2">
                <TrendingUp className="h-4 w-4" /> Billed Revenue
              </div>
              <div className="text-3xl font-bold text-white">
                <IndianRupee className="inline h-6 w-6 text-slate-500"/> {plSummary.total_revenue || 0}
              </div>
              <p className="text-xs text-slate-500 mt-2">From Finalized Invoices</p>
            </div>
            
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
              <div className="flex items-center gap-2 text-sm font-medium text-rose-400 mb-2">
                <TrendingDown className="h-4 w-4" /> Vendor Costs
              </div>
              <div className="text-3xl font-bold text-white">
                <IndianRupee className="inline h-6 w-6 text-slate-500"/> {plSummary.total_payables || 0}
              </div>
              <p className="text-xs text-slate-500 mt-2">From Approved Payables</p>
            </div>
            
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
              <div className="flex items-center gap-2 text-sm font-medium text-amber-400 mb-2">
                <Activity className="h-4 w-4" /> Operational Expenses
              </div>
              <div className="text-3xl font-bold text-white">
                <IndianRupee className="inline h-6 w-6 text-slate-500"/> {plSummary.total_expenses || 0}
              </div>
              <p className="text-xs text-slate-500 mt-2">Fuel, Tolls, Maint.</p>
            </div>
            
            <div className="rounded-2xl border border-slate-800 bg-indigo-900/20 p-6">
              <div className="flex items-center gap-2 text-sm font-medium text-indigo-400 mb-2">
                <IndianRupee className="h-4 w-4" /> Gross Margin
              </div>
              <div className="text-3xl font-bold text-white">
                <IndianRupee className="inline h-6 w-6 text-indigo-500"/> {plSummary.gross_profit || 0}
              </div>
              <p className="text-xs text-indigo-300 mt-2">
                {plSummary.total_revenue > 0 ? 
                  ((plSummary.gross_profit / plSummary.total_revenue) * 100).toFixed(1) + '%' 
                  : '0%'} Margin
              </p>
            </div>
          </div>
          
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
            <div className="flex items-center gap-2 text-slate-400 mb-4">
              <AlertCircle className="h-5 w-5" />
              <h3 className="font-semibold text-white">Financial Independence Note</h3>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed">
              In accordance with the Zolexora TMS financial architecture, <strong>Customer Price</strong> is completely decoupled from <strong>Vendor Cost</strong>. 
              The revenue figures above are derived exclusively from the Customer-side deterministic Rate Cards evaluated at Duty completion, 
              while the Vendor Costs are derived from the independent Provider-side Rate Cards (e.g. for DCOs or Fleet Owners).
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
