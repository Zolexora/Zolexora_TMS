import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CreditCard, IndianRupee, Plus, Upload } from 'lucide-react';
import { apiClient } from '../../lib/api';

export function PaymentsPage() {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  
  // Simple form state
  const [customerId] = useState('');
  const [invoiceId, setInvoiceId] = useState('');
  const [amount, setAmount] = useState('');
  const [paymentMethod] = useState('BANK_TRANSFER');
  const [refId, setRefId] = useState('');

  const { data: payments, isLoading } = useQuery({
    queryKey: ['payments'],
    queryFn: () => apiClient<any[]>('/api/v1/payments')
  });

  const { data: invoices } = useQuery({
    queryKey: ['invoices'],
    queryFn: () => apiClient<any[]>('/api/v1/invoices')
  });
  
  const allocatableInvoices = invoices?.filter(i => ['FINALIZED', 'PARTIALLY_PAID'].includes(i.status)) || [];

  const createMutation = useMutation({
    mutationFn: () => apiClient('/api/v1/payments', {
      method: 'POST',
      body: JSON.stringify({
        customer_id: customerId || "00000000-0000-0000-0000-000000000000",
        provider: "BANK",
        provider_transaction_id: refId,
        payment_method: paymentMethod,
        amount: parseFloat(amount),
        currency: "INR",
        payment_date: new Date().toISOString().split('T')[0],
        notes: "",
        allocations: invoiceId ? [{ invoice_id: invoiceId, amount_allocated: parseFloat(amount) }] : []
      })
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments'] });
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      queryClient.invalidateQueries({ queryKey: ['receivables'] });
      setModalOpen(false);
      alert('Payment recorded successfully.');
    }
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Customer Payments</h1>
          <p className="text-sm text-slate-400">Record payments received and allocate to invoices.</p>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={() => setModalOpen(true)}
            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 transition"
          >
            <Plus className="h-4 w-4" />
            Record Payment
          </button>
          <button 
            className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-700 transition"
            onClick={() => alert("CSV Upload reconciliation coming soon!")}
          >
            <Upload className="h-4 w-4" />
            Reconcile CSV
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12">
          <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-t-2 border-indigo-500"></div>
        </div>
      ) : payments?.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center">
          <div className="rounded-2xl bg-indigo-500/10 p-4 text-indigo-400 mb-4">
            <CreditCard className="h-8 w-8" />
          </div>
          <h3 className="text-base font-semibold text-white">No payments recorded</h3>
          <p className="mt-1 text-sm text-slate-400">Record customer payments to see them here.</p>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-800 bg-slate-900/80 text-slate-400">
              <tr>
                <th className="p-4 font-medium">Ref ID</th>
                <th className="p-4 font-medium">Date</th>
                <th className="p-4 font-medium">Method</th>
                <th className="p-4 font-medium text-right">Amount</th>
                <th className="p-4 font-medium text-right">Unallocated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {payments?.map(pay => (
                <tr key={pay.id} className="hover:bg-slate-800/30 transition">
                  <td className="p-4 text-white font-mono">{pay.provider_transaction_id || pay.id.substring(0,8)}</td>
                  <td className="p-4 text-slate-300">{pay.payment_date}</td>
                  <td className="p-4 text-slate-300">{pay.payment_method}</td>
                  <td className="p-4 text-white font-semibold text-right">
                    <IndianRupee className="inline h-3 w-3 text-slate-500"/> {pay.amount}
                  </td>
                  <td className="p-4 text-amber-400 font-semibold text-right">
                    <IndianRupee className="inline h-3 w-3 text-slate-500"/> {pay.unallocated_amount}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-white">Record Payment</h2>
            <div className="mt-4 space-y-4">
              <div>
                <label className="mb-1 block text-sm text-slate-300">Amount</label>
                <input type="number" value={amount} onChange={e => setAmount(e.target.value)} className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-white" />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-300">Reference / UTR</label>
                <input type="text" value={refId} onChange={e => setRefId(e.target.value)} className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-white" />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-300">Allocate to Invoice (Optional)</label>
                <select value={invoiceId} onChange={e => setInvoiceId(e.target.value)} className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-white">
                  <option value="">-- No Allocation --</option>
                  {allocatableInvoices.map(inv => (
                    <option key={inv.id} value={inv.id}>{inv.invoice_number} (Due: {inv.amount_due})</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button onClick={() => setModalOpen(false)} className="rounded-lg px-4 py-2 text-sm text-slate-300 hover:bg-slate-800">Cancel</button>
              <button onClick={() => createMutation.mutate()} disabled={createMutation.isPending || !amount} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-500">Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
