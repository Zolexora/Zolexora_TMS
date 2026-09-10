import { useQuery } from '@tanstack/react-query';
import { Receipt, Plus } from 'lucide-react';
import { apiClient } from '../../lib/api';

export function PayablesPage() {
  const { data: payables, isLoading } = useQuery({
    queryKey: ['payables'],
    queryFn: () => apiClient<any[]>('/api/v1/payables')
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Payables & Vendor Settlements</h1>
          <p className="text-sm text-slate-400">Track and settle amounts owed to vendors and fleet drivers.</p>
        </div>
        <button className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition">
          <Plus className="h-4 w-4" />
          Create Payable
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12">
          <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-t-2 border-indigo-500"></div>
        </div>
      ) : payables?.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center">
          <div className="rounded-2xl bg-indigo-500/10 p-4 text-indigo-400 mb-4">
            <Receipt className="h-8 w-8" />
          </div>
          <h3 className="text-base font-semibold text-white">No payables found</h3>
          <p className="mt-1 text-sm text-slate-400 max-w-sm">
            Create payables to manage vendor invoices and driver allowances.
          </p>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 overflow-hidden">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-6 py-4 font-medium">Ref Number</th>
                <th className="px-6 py-4 font-medium">Beneficiary</th>
                <th className="px-6 py-4 font-medium">Grand Total</th>
                <th className="px-6 py-4 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {payables?.map((payable) => (
                <tr key={payable.id} className="hover:bg-slate-800/30 transition">
                  <td className="px-6 py-4 font-medium">{payable.reference_number}</td>
                  <td className="px-6 py-4">{payable.vendor_id ? 'Vendor' : 'Driver'}</td>
                  <td className="px-6 py-4 font-medium text-white">{payable.currency} {payable.grand_total}</td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-400">
                      {payable.status}
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
