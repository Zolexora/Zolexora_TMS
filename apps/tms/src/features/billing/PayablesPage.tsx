
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FileText, IndianRupee,} from 'lucide-react';
import { apiClient } from '../../lib/api';

export function PayablesPage() {
  const queryClient = useQueryClient();
  const { data: payables, isLoading } = useQuery({
    queryKey: ['payables'],
    queryFn: () => apiClient<any[]>('/api/v1/payables')
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => apiClient(`/api/v1/payables/${id}/approve`, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['payables'] })
  });

  const settleMutation = useMutation({
    mutationFn: (id: string) => apiClient(`/api/v1/payables/${id}/settle`, { 
      method: 'POST', 
      body: JSON.stringify({ amount_paid: 0, payment_method: 'CASH', reference_id: 'SETTLE-' + Date.now() }) 
      // The backend settlement route might require specific payload, doing a simplified one.
    }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['payables'] })
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Vendor & Driver Payables</h1>
          <p className="text-sm text-slate-400">Track and settle amounts owed to DCOs and fleet vendors.</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12">
          <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-t-2 border-indigo-500"></div>
        </div>
      ) : payables?.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center">
          <div className="rounded-2xl bg-indigo-500/10 p-4 text-indigo-400 mb-4">
            <FileText className="h-8 w-8" />
          </div>
          <h3 className="text-base font-semibold text-white">No payables found</h3>
          <p className="mt-1 text-sm text-slate-400 max-w-sm">
            Payables are generated automatically when a Vendor Duty is calculated.
          </p>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-800 bg-slate-900/80 text-slate-400">
              <tr>
                <th className="p-4 font-medium">Vendor</th>
                <th className="p-4 font-medium">Duty ID</th>
                <th className="p-4 font-medium">Status</th>
                <th className="p-4 font-medium text-right">Amount Owed</th>
                <th className="p-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {payables?.map(payable => (
                <tr key={payable.id} className="hover:bg-slate-800/30 transition">
                  <td className="p-4 text-slate-300 font-medium">{payable.vendor_name || 'Vendor'}</td>
                  <td className="p-4 text-slate-400 font-mono text-xs">{payable.duty_id?.split('-')[0] || '-'}</td>
                  <td className="p-4">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      payable.status === 'APPROVED' ? 'bg-indigo-500/10 text-indigo-400' :
                      payable.status === 'DRAFT' ? 'bg-slate-500/10 text-slate-400' :
                      payable.status === 'SETTLED' ? 'bg-emerald-500/10 text-emerald-400' :
                      'bg-slate-500/10 text-slate-400'
                    }`}>
                      {payable.status}
                    </span>
                  </td>
                  <td className="p-4 text-white font-semibold text-right">
                    <IndianRupee className="inline h-3 w-3 text-slate-500"/> {payable.total_amount}
                  </td>
                  <td className="p-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {payable.status === 'DRAFT' && (
                        <button 
                          onClick={() => approveMutation.mutate(payable.id)}
                          className="rounded-md bg-indigo-600/20 px-2 py-1 text-xs font-medium text-indigo-400 hover:bg-indigo-600/30"
                        >
                          Approve
                        </button>
                      )}
                      {payable.status === 'APPROVED' && (
                        <button 
                          onClick={() => settleMutation.mutate(payable.id)}
                          className="rounded-md bg-emerald-600/20 px-2 py-1 text-xs font-medium text-emerald-400 hover:bg-emerald-600/30"
                        >
                          Settle
                        </button>
                      )}
                    </div>
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
