
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FileText, IndianRupee, Eye} from 'lucide-react';
import { apiClient } from '../../lib/api';

export function InvoicesPage() {
  const queryClient = useQueryClient();
  const { data: invoices, isLoading } = useQuery({
    queryKey: ['invoices'],
    queryFn: () => apiClient<any[]>('/api/v1/invoices')
  });

  const issueMutation = useMutation({
    mutationFn: (id: string) => apiClient(`/api/v1/invoices/${id}/issue`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
    }
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Invoices</h1>
          <p className="text-sm text-slate-400">Manage customer billing and track outstanding revenue.</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12">
          <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-t-2 border-indigo-500"></div>
        </div>
      ) : invoices?.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center">
          <div className="rounded-2xl bg-indigo-500/10 p-4 text-indigo-400 mb-4">
            <FileText className="h-8 w-8" />
          </div>
          <h3 className="text-base font-semibold text-white">No invoices issued</h3>
          <p className="mt-1 text-sm text-slate-400 max-w-sm">
            Generate invoices from the Billing Pipelines tab to see them here.
          </p>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-800 bg-slate-900/80 text-slate-400">
              <tr>
                <th className="p-4 font-medium">Invoice #</th>
                <th className="p-4 font-medium">Customer</th>
                <th className="p-4 font-medium">Status</th>
                <th className="p-4 font-medium text-right">Amount</th>
                <th className="p-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {invoices?.map(invoice => (
                <tr key={invoice.id} className="hover:bg-slate-800/30 transition">
                  <td className="p-4 text-white font-mono font-medium">{invoice.invoice_number || 'DRAFT'}</td>
                  <td className="p-4 text-slate-300 font-medium">{invoice.customer_name || 'Customer'}</td>
                  <td className="p-4">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      invoice.status === 'FINALIZED' ? 'bg-emerald-500/10 text-emerald-400' :
                      invoice.status === 'DRAFT' ? 'bg-amber-500/10 text-amber-400' :
                      invoice.status === 'PAID' ? 'bg-indigo-500/10 text-indigo-400' :
                      'bg-slate-500/10 text-slate-400'
                    }`}>
                      {invoice.status}
                    </span>
                  </td>
                  <td className="p-4 text-white font-semibold text-right">
                    <IndianRupee className="inline h-3 w-3 text-slate-500"/> {invoice.total_amount || 0}
                  </td>
                  <td className="p-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {invoice.status === 'DRAFT' && (
                        <button 
                          onClick={() => issueMutation.mutate(invoice.id)}
                          disabled={issueMutation.isPending}
                          className="rounded-md bg-emerald-600/20 px-2 py-1 text-xs font-medium text-emerald-400 hover:bg-emerald-600/30"
                        >
                          Issue / Finalize
                        </button>
                      )}
                      <button className="text-slate-400 hover:text-white">
                        <Eye className="h-4 w-4" />
                      </button>
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
