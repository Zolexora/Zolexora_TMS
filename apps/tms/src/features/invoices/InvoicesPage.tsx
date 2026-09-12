import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FileText, IndianRupee, Download, XCircle, PlusCircle, MinusCircle } from 'lucide-react';
import { apiClient } from '../../lib/api';

export function InvoicesPage() {
  const queryClient = useQueryClient();
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | null>(null);
  const [cancelModalOpen, setCancelModalOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState('');
  
  const [adjModalOpen, setAdjModalOpen] = useState(false);
  const [adjType, setAdjType] = useState<'CREDIT' | 'DEBIT'>('CREDIT');
  const [adjAmount, setAdjAmount] = useState('');
  const [adjReason, setAdjReason] = useState('');

  const { data: invoices, isLoading } = useQuery({
    queryKey: ['invoices'],
    queryFn: () => apiClient<any[]>('/api/v1/invoices')
  });

  const issueMutation = useMutation({
    mutationFn: (id: string) => apiClient(`/api/v1/invoices/${id}/finalize`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      queryClient.invalidateQueries({ queryKey: ['billing'] });
      queryClient.invalidateQueries({ queryKey: ['receivables'] });
      queryClient.invalidateQueries({ queryKey: ['pnl'] });
      alert('Invoice finalized successfully.');
    }
  });

  const pdfMutation = useMutation({
    mutationFn: (id: string) => apiClient<{pdf_url: string}>(`/api/v1/invoices/${id}/pdf`, { method: 'POST' }),
    onSuccess: (data) => {
      window.open(data.pdf_url, '_blank');
    }
  });

  const cancelMutation = useMutation({
    mutationFn: () => apiClient(`/api/v1/invoices/${selectedInvoiceId}/cancel?reason=${encodeURIComponent(cancelReason)}`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      queryClient.invalidateQueries({ queryKey: ['billing'] });
      queryClient.invalidateQueries({ queryKey: ['receivables'] });
      queryClient.invalidateQueries({ queryKey: ['pnl'] });
      setCancelModalOpen(false);
      setCancelReason('');
      setSelectedInvoiceId(null);
      alert('Invoice cancelled successfully.');
    }
  });

  const adjMutation = useMutation({
    mutationFn: () => apiClient('/api/v1/adjustments', {
      method: 'POST',
      body: JSON.stringify({
        invoice_id: selectedInvoiceId,
        adjustment_type: adjType,
        amount: parseFloat(adjAmount),
        reason: adjReason
      })
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      queryClient.invalidateQueries({ queryKey: ['receivables'] });
      queryClient.invalidateQueries({ queryKey: ['pnl'] });
      setAdjModalOpen(false);
      setAdjAmount('');
      setAdjReason('');
      setSelectedInvoiceId(null);
      alert('Adjustment note created successfully.');
    }
  });

  const openCancel = (id: string) => {
    setSelectedInvoiceId(id);
    setCancelReason('');
    setCancelModalOpen(true);
  };

  const openAdj = (id: string, type: 'CREDIT' | 'DEBIT') => {
    setSelectedInvoiceId(id);
    setAdjType(type);
    setAdjAmount('');
    setAdjReason('');
    setAdjModalOpen(true);
  };

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
            Generate invoices from the Billing tab to see them here.
          </p>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-800 bg-slate-900/80 text-slate-400">
              <tr>
                <th className="p-4 font-medium">Invoice #</th>
                <th className="p-4 font-medium">Date</th>
                <th className="p-4 font-medium">Due Date</th>
                <th className="p-4 font-medium">Status</th>
                <th className="p-4 font-medium text-right">Amount Due</th>
                <th className="p-4 font-medium text-right">Total</th>
                <th className="p-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {invoices?.map(invoice => (
                <tr key={invoice.id} className="hover:bg-slate-800/30 transition">
                  <td className="p-4 text-white font-mono font-medium">{invoice.invoice_number || 'DRAFT'}</td>
                  <td className="p-4 text-slate-300 font-medium">{invoice.invoice_date}</td>
                  <td className="p-4 text-slate-300 font-medium">{invoice.due_date}</td>
                  <td className="p-4">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      invoice.status === 'FINALIZED' ? 'bg-blue-500/10 text-blue-400' :
                      invoice.status === 'DRAFT' ? 'bg-slate-500/10 text-slate-400' :
                      invoice.status === 'PARTIALLY_PAID' ? 'bg-amber-500/10 text-amber-400' :
                      invoice.status === 'PAID' ? 'bg-emerald-500/10 text-emerald-400' :
                      'bg-red-500/10 text-red-400'
                    }`}>
                      {invoice.status}
                    </span>
                  </td>
                  <td className="p-4 text-amber-400 font-semibold text-right">
                    <IndianRupee className="inline h-3 w-3 text-slate-500"/> {invoice.amount_due || 0}
                  </td>
                  <td className="p-4 text-white font-semibold text-right">
                    <IndianRupee className="inline h-3 w-3 text-slate-500"/> {invoice.grand_total || 0}
                  </td>
                  <td className="p-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {invoice.status === 'DRAFT' && (
                        <button 
                          onClick={() => issueMutation.mutate(invoice.id)}
                          disabled={issueMutation.isPending}
                          className="rounded-md bg-emerald-600/20 px-2 py-1 text-xs font-medium text-emerald-400 hover:bg-emerald-600/30"
                        >
                          Finalize
                        </button>
                      )}
                      {['FINALIZED', 'PARTIALLY_PAID', 'PAID'].includes(invoice.status) && (
                        <>
                          <button 
                            onClick={() => pdfMutation.mutate(invoice.id)}
                            disabled={pdfMutation.isPending}
                            title="Generate/View PDF"
                            className="rounded-md bg-blue-600/20 p-1 text-blue-400 hover:bg-blue-600/30"
                          >
                            <Download className="h-4 w-4" />
                          </button>
                          <button 
                            onClick={() => openAdj(invoice.id, 'CREDIT')}
                            title="Credit Note"
                            className="rounded-md bg-indigo-600/20 p-1 text-indigo-400 hover:bg-indigo-600/30"
                          >
                            <MinusCircle className="h-4 w-4" />
                          </button>
                          <button 
                            onClick={() => openAdj(invoice.id, 'DEBIT')}
                            title="Debit Note"
                            className="rounded-md bg-indigo-600/20 p-1 text-indigo-400 hover:bg-indigo-600/30"
                          >
                            <PlusCircle className="h-4 w-4" />
                          </button>
                        </>
                      )}
                      {['FINALIZED'].includes(invoice.status) && (
                        <button 
                          onClick={() => openCancel(invoice.id)}
                          title="Cancel Invoice"
                          className="rounded-md bg-red-600/20 p-1 text-red-400 hover:bg-red-600/30"
                        >
                          <XCircle className="h-4 w-4" />
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

      {/* Modals */}
      {cancelModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-white">Cancel Invoice</h2>
            <div className="mt-2 rounded-lg bg-amber-500/10 p-3 text-sm text-amber-400 border border-amber-500/20">
              Warning: This action changes the invoice lifecycle and creates an audit record. The snapshot will be unlocked.
            </div>
            <div className="mt-4">
              <label className="mb-1 block text-sm font-medium text-slate-300">Reason</label>
              <textarea
                value={cancelReason}
                onChange={e => setCancelReason(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-white focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                rows={3}
                required
              />
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setCancelModalOpen(false)}
                className="rounded-lg px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800"
              >
                Keep Invoice
              </button>
              <button
                onClick={() => cancelMutation.mutate()}
                disabled={!cancelReason || cancelMutation.isPending}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-500 disabled:opacity-50"
              >
                {cancelMutation.isPending ? 'Cancelling...' : 'Cancel Invoice'}
              </button>
            </div>
          </div>
        </div>
      )}

      {adjModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-white">Create {adjType === 'CREDIT' ? 'Credit' : 'Debit'} Note</h2>
            <div className="mt-4 space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-300">Amount</label>
                <input
                  type="number"
                  value={adjAmount}
                  onChange={e => setAdjAmount(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-white focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-300">Reason / Notes</label>
                <textarea
                  value={adjReason}
                  onChange={e => setAdjReason(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-white focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  rows={2}
                  required
                />
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setAdjModalOpen(false)}
                className="rounded-lg px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                onClick={() => adjMutation.mutate()}
                disabled={!adjAmount || !adjReason || adjMutation.isPending}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                {adjMutation.isPending ? 'Saving...' : 'Create Note'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
