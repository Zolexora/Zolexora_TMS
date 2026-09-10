import { useQuery } from '@tanstack/react-query';
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';
import { apiClient } from '../../lib/api';

export function PnLReportsPage() {
  const { data: pnl, isLoading } = useQuery({
    queryKey: ['pnl-summary'],
    queryFn: () => apiClient<any>('/api/v1/pl/summary')
  });

  if (isLoading) {
    return (
      <div className="flex justify-center p-12">
        <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-t-2 border-indigo-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">P&L Financial Reports</h1>
          <p className="text-sm text-slate-400">High-level financial health directly calculated from operations.</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
          <div className="flex items-center gap-3 text-slate-400 mb-2">
            <DollarSign className="h-5 w-5" />
            <h3 className="font-medium">Total Net Revenue</h3>
          </div>
          <p className="text-3xl font-bold text-white">{pnl?.currency || 'INR'} {pnl?.total_revenue_net || '0.00'}</p>
          <p className="text-xs text-slate-500 mt-2">From finalized invoices</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
          <div className="flex items-center gap-3 text-slate-400 mb-2">
            <TrendingDown className="h-5 w-5 text-rose-400" />
            <h3 className="font-medium">Direct Costs</h3>
          </div>
          <p className="text-3xl font-bold text-white">{pnl?.currency || 'INR'} {pnl?.total_direct_costs || '0.00'}</p>
          <p className="text-xs text-slate-500 mt-2">Payables and operational expenses</p>
        </div>

        <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3 text-emerald-400">
              <TrendingUp className="h-5 w-5" />
              <h3 className="font-medium">Gross Profit</h3>
            </div>
            <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-400">
              {pnl?.gross_margin_percentage || '0.00'}% Margin
            </span>
          </div>
          <p className="text-3xl font-bold text-emerald-400">{pnl?.currency || 'INR'} {pnl?.gross_profit || '0.00'}</p>
        </div>
      </div>
      
      {/* Visual placeholder for charts or breakdowns */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 mt-6 min-h-[300px] flex items-center justify-center">
         <p className="text-slate-500">Detailed line-item breakdown coming soon...</p>
      </div>
    </div>
  );
}
