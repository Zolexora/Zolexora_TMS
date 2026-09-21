import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Receipt, IndianRupee, Download, CheckCircle, CreditCard } from 'lucide-react';
import { apiClient } from '../../lib/api';

export function PayablesPage() {
  const queryClient = useQueryClient();
  const [settleModalOpen, setSettleModalOpen] = useState(false);
  const [selectedPayableId, setSelectedPayableId] = useState<string | null>(null);
  const [amount, setAmount] = useState('');
  const [reference, setReference] = useState('');

  const { data: payables, isLoading } = useQuery({
    queryKey: ['payables'],
    queryFn: () => apiClient<any[]>('/api/v1/payables')
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => apiClient(`/api/v1/payables/${id}/approve`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payables'] });
      alert('Payable approved.');
    }
  });

  const pdfMutation = useMutation({
    mutationFn: (id: string) => apiClient<{pdf_url: string}>(`/api/v1/payables/${id}/pdf`, { method: 'POST' }),
    onSuccess: (data) => {
      window.open(data.pdf_url, '_blank');
    }
  });

  const settleMutation = useMutation({
    mutationFn: () => apiClient(`/api/v1/payables/${selectedPayableId}/settlements`, {
      method: 'POST',
      body: JSON.stringify({
        amount: parseFloat(amount),
        settlement_date: new Date().toISOString().split('T')[0],
        payment_reference: reference,
        notes: ''
      })
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payables'] });
      setSettleModalOpen(false);
      setAmount('');
      setReference('');
      alert('Settlement recorded successfully.');
    }
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Vendor Payables & Settlements</h1>
          <p className="text-sm text-slate-400">Manage outgoing payments to DCOs and Fleet Vendors.</p>
        </div>
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
          <p className="mt-1 text-sm text-slate-400">Vendor payables will appear here when generated.</p>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-800 bg-slate-900/80 text-slate-400">
              <tr>
                <th className="p-4 font-medium">Ref #</th>
                <th className="p-4 font-medium">Duty ID</th>
                <th className="p-4 font-medium">Status</th>
                <th className="p-4 font-medium text-right">Subtotal</th>
                <th className="p-4 font-medium text-right">Deductions</th>
                <th className="p-4 font-medium text-right">Net Payable</th>
                <th className="p-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {payables?.map(payable => (
                <tr key={payable.id} className="hover:bg-slate-800/30 transition">
                  <td className="p-4 text-white font-mono">{payable.reference_number || '-'}</td>
                  <td className="p-4 text-slate-300 font-mono text-xs">{payable.duty_id?.split('-')[0] || '-'}</td>
                  <td className="p-4">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      payable.status === 'APPROVED' ? 'bg-blue-500/10 text-blue-400' :
                      payable.status === 'DRAFT' ? 'bg-slate-500/10 text-slate-400' :
                      payable.status === 'SETTLED' ? 'bg-emerald-500/10 text-emerald-400' :
                      'bg-slate-500/10 text-slate-400'
                    }`}>
                      {payable.status}
                    </span>
                  </td>
                  <td className="p-4 text-slate-300 text-right"><IndianRupee className="inline h-3 w-3 text-slate-500"/> {payable.subtotal || 0}</td>
                  <td className="p-4 text-red-400 text-right"><IndianRupee className="inline h-3 w-3 text-slate-500"/> {payable.deductions || 0}</td>
                  <td className="p-4 text-white font-semibold text-right"><IndianRupee className="inline h-3 w-3 text-slate-500"/> {payable.grand_total || 0}</td>
                  <td className="p-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {payable.status === 'DRAFT' && (
                        <button onClick={() => approveMutation.mutate(payable.id)} disabled={approveMutation.isPending} className="rounded-md bg-emerald-600/20 p-1 text-emerald-400 hover:bg-emerald-600/30" title="Approve">
                          <CheckCircle className="h-4 w-4" />
                        </button>
                      )}
                      {payable.status === 'APPROVED' && (
                        <button onClick={() => { setSelectedPayableId(payable.id); setSettleModalOpen(true); }} className="rounded-md bg-blue-600/20 p-1 text-blue-400 hover:bg-blue-600/30" title="Record Settlement Payment">
                          <CreditCard className="h-4 w-4" />
                        </button>
                      )}
                      <button onClick={() => pdfMutation.mutate(payable.id)} disabled={pdfMutation.isPending} className="rounded-md bg-slate-600/20 p-1 text-slate-400 hover:bg-slate-600/30" title="Generate PDF Document">
                        <Download className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {settleModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-white">Record Settlement</h2>
            <div className="mt-4 space-y-4">
              <div>
                <label className="mb-1 block text-sm text-slate-300">Amount Paid</label>
                <input type="number" value={amount} onChange={e => setAmount(e.target.value)} className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-white" />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-300">Bank Reference</label>
                <input type="text" value={reference} onChange={e => setReference(e.target.value)} className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-white" />
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button onClick={() => setSettleModalOpen(false)} className="rounded-lg px-4 py-2 text-sm text-slate-300 hover:bg-slate-800">Cancel</button>
              <button onClick={() => settleMutation.mutate()} disabled={settleMutation.isPending || !amount} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-500">Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
