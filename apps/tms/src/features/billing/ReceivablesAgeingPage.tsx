import { useQuery } from '@tanstack/react-query';
import { IndianRupee, TrendingUp, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { apiClient } from '../../lib/api';

export function ReceivablesAgeingPage() {
  const { data: buckets, isLoading } = useQuery({
    queryKey: ['receivables-ageing'],
    queryFn: () => apiClient<any>('/api/v1/invoices/reports/receivables-ageing')
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Receivables Ageing Dashboard</h1>
        <p className="text-sm text-slate-400">Track outstanding customer invoices by age bucket.</p>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12">
          <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-t-2 border-indigo-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
            <div className="flex items-center gap-4">
              <div className="rounded-xl bg-blue-500/10 p-3 text-blue-400">
                <TrendingUp className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Total Outstanding</p>
                <p className="text-2xl font-bold text-white flex items-center">
                  <IndianRupee className="h-5 w-5 mr-1 text-slate-500"/>
                  {buckets?.total_outstanding || 0}
                </p>
              </div>
            </div>
          </div>
          
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
            <div className="flex items-center gap-4">
              <div className="rounded-xl bg-emerald-500/10 p-3 text-emerald-400">
                <CheckCircle className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm text-slate-400">Current (Not Due)</p>
                <p className="text-2xl font-bold text-white flex items-center">
                  <IndianRupee className="h-5 w-5 mr-1 text-slate-500"/>
                  {buckets?.current || 0}
                </p>
              </div>
            </div>
          </div>
          
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
            <div className="flex items-center gap-4">
              <div className="rounded-xl bg-amber-500/10 p-3 text-amber-400">
                <Clock className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm text-slate-400">1 - 30 Days</p>
                <p className="text-2xl font-bold text-white flex items-center">
                  <IndianRupee className="h-5 w-5 mr-1 text-slate-500"/>
                  {buckets?.['1_30_days'] || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
            <div className="flex items-center gap-4">
              <div className="rounded-xl bg-orange-500/10 p-3 text-orange-400">
                <AlertTriangle className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm text-slate-400">31 - 60 Days</p>
                <p className="text-2xl font-bold text-white flex items-center">
                  <IndianRupee className="h-5 w-5 mr-1 text-slate-500"/>
                  {buckets?.['31_60_days'] || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
            <div className="flex items-center gap-4">
              <div className="rounded-xl bg-red-500/10 p-3 text-red-400">
                <AlertTriangle className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm text-slate-400">61 - 90 Days</p>
                <p className="text-2xl font-bold text-white flex items-center">
                  <IndianRupee className="h-5 w-5 mr-1 text-slate-500"/>
                  {buckets?.['61_90_days'] || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-red-900/50 bg-red-950/20 p-6">
            <div className="flex items-center gap-4">
              <div className="rounded-xl bg-red-500/20 p-3 text-red-500">
                <AlertTriangle className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm text-red-400">Over 90 Days</p>
                <p className="text-2xl font-bold text-white flex items-center">
                  <IndianRupee className="h-5 w-5 mr-1 text-red-500"/>
                  {buckets?.['over_90_days'] || 0}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
