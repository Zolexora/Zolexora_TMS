import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { FileText,IndianRupee } from 'lucide-react';
import { apiClient } from '../../lib/api';

export function BillingPage() {
  const queryClient = useQueryClient();
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const { data: billingRecords, isLoading } = useQuery({
    queryKey: ['billing'],
    queryFn: () => apiClient<any[]>('/api/v1/billing')
  });

  const generateMutation = useMutation({
    mutationFn: (ids: string[]) => apiClient('/api/v1/invoices', {
      method: 'POST',
      body: JSON.stringify({ billing_record_ids: ids })
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['billing'] });
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      setSelectedIds([]);
      alert('Invoice created successfully! View it in the Invoices tab.');
    }
  });

  const pendingRecords = billingRecords?.filter(r => r.status === 'PENDING') || [];
  
  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setSelectedIds(pendingRecords.map(r => r.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelect = (id: string) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Billing Pipelines</h1>
          <p className="text-sm text-slate-400">View pending financial snapshots ready to be consolidated into invoices.</p>
        </div>
        <button
          onClick={() => generateMutation.mutateAsync(selectedIds)}
          disabled={selectedIds.length === 0 || generateMutation.isPending}
          className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition disabled:opacity-50"
        >
          {generateMutation.isPending ? 'Generating...' : `Generate Invoice (${selectedIds.length})`}
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12">
          <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-t-2 border-indigo-500"></div>
        </div>
      ) : pendingRecords.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center">
          <div className="rounded-2xl bg-indigo-500/10 p-4 text-indigo-400 mb-4">
            <FileText className="h-8 w-8" />
          </div>
          <h3 className="text-base font-semibold text-white">No billable duties</h3>
          <p className="mt-1 text-sm text-slate-400 max-w-sm">
            Completed duties will appear here once their financial snapshots are calculated.
          </p>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-800 bg-slate-900/80 text-slate-400">
              <tr>
                <th className="p-4 w-12 text-center">
                  <input 
                    type="checkbox" 
                    onChange={handleSelectAll} 
                    checked={selectedIds.length === pendingRecords.length && pendingRecords.length > 0}
                    className="rounded border-slate-700 bg-slate-800 text-indigo-500" 
                  />
                </th>
                <th className="p-4 font-medium">Duty ID</th>
                <th className="p-4 font-medium">Customer</th>
                <th className="p-4 font-medium text-right">Taxable</th>
                <th className="p-4 font-medium text-right">Tax</th>
                <th className="p-4 font-medium text-right">Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {pendingRecords.map(record => (
                <tr key={record.id} className="hover:bg-slate-800/30 transition">
                  <td className="p-4 text-center">
                    <input 
                      type="checkbox" 
                      checked={selectedIds.includes(record.id)}
                      onChange={() => handleSelect(record.id)}
                      className="rounded border-slate-700 bg-slate-800 text-indigo-500" 
                    />
                  </td>
                  <td className="p-4 text-slate-300 font-mono text-xs">{record.duty_id.split('-')[0]}</td>
                  <td className="p-4 text-slate-300 font-medium">{record.customer_name || 'Unknown'}</td>
                  <td className="p-4 text-slate-300 text-right"><IndianRupee className="inline h-3 w-3 text-slate-500"/> {record.snapshot?.taxable_amount || 0}</td>
                  <td className="p-4 text-slate-300 text-right"><IndianRupee className="inline h-3 w-3 text-slate-500"/> {record.snapshot?.tax_amount || 0}</td>
                  <td className="p-4 text-white font-semibold text-right"><IndianRupee className="inline h-3 w-3 text-slate-500"/> {record.snapshot?.grand_total || 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
