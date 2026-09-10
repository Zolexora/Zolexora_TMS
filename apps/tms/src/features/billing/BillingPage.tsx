import { useQuery } from '@tanstack/react-query';
import { FileText } from 'lucide-react';
import { apiClient } from '../../lib/api';

export function BillingPage() {
  const { data: billingRecords, isLoading } = useQuery({
    queryKey: ['billing'],
    queryFn: () => apiClient<any[]>('/api/v1/billing')
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Billing Pipelines</h1>
          <p className="text-sm text-slate-400">View pending financial snapshots ready to be consolidated into invoices.</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12">
          <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-t-2 border-indigo-500"></div>
        </div>
      ) : billingRecords?.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center">
          <div className="rounded-2xl bg-indigo-500/10 p-4 text-indigo-400 mb-4">
            <FileText className="h-8 w-8" />
          </div>
          <h3 className="text-base font-semibold text-white">No pending billing records</h3>
          <p className="mt-1 text-sm text-slate-400 max-w-sm">
            Completed duties will automatically generate financial snapshots and appear here.
          </p>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 overflow-hidden">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-6 py-4 font-medium">Record ID</th>
                <th className="px-6 py-4 font-medium">Customer</th>
                <th className="px-6 py-4 font-medium">Amount Due</th>
                <th className="px-6 py-4 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {billingRecords?.map((record) => (
                <tr key={record.id} className="hover:bg-slate-800/30 transition">
                  <td className="px-6 py-4 font-mono text-xs">{record.id.substring(0,8)}</td>
                  <td className="px-6 py-4">{record.customer_id}</td>
                  <td className="px-6 py-4 font-medium text-white">{record.currency} {record.total_amount_due}</td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-semibold text-amber-400">
                      PENDING
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
