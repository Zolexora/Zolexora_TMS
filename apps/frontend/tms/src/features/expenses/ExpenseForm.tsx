import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { X } from 'lucide-react';
import { apiClient } from '../../lib/api';

export function ExpenseForm({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [error, setError] = useState('');
  
  const [category, setCategory] = useState('FUEL');
  const [amount, setAmount] = useState(0);
  const [description, setDescription] = useState('');
  const [dutyId, setDutyId] = useState('');

  const mutation = useMutation({
    mutationFn: (data: any) => apiClient('/api/v1/expenses', { method: 'POST', body: JSON.stringify(data) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] });
      onClose();
    },
    onError: (err: any) => setError(err.message || 'Failed to log expense')
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate({ 
      category, 
      amount, 
      description, 
      duty_id: dutyId || null,
      incurred_date: new Date().toISOString()
    });
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-950 shadow-2xl overflow-hidden flex flex-col">
        <div className="p-5 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
          <h2 className="text-lg font-bold text-white">Log Expense</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-white"><X className="h-5 w-5" /></button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && <div className="rounded-lg bg-red-500/10 p-3 text-sm text-red-500 border border-red-500/20">{error}</div>}
          
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Category</label>
            <select value={category} onChange={e => setCategory(e.target.value)} className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-white">
              <option value="FUEL">Fuel</option>
              <option value="TOLL">Toll</option>
              <option value="PARKING">Parking</option>
              <option value="MAINTENANCE">Maintenance</option>
              <option value="DRIVER_ALLOWANCE">Driver Allowance (Batta)</option>
              <option value="OTHER">Other</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Amount (₹)</label>
            <input type="number" required min="0.01" step="0.01" value={amount} onChange={e => setAmount(parseFloat(e.target.value))} className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-white" />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Description</label>
            <input type="text" required value={description} onChange={e => setDescription(e.target.value)} className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-white" />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Duty ID (Optional)</label>
            <input type="text" placeholder="UUID of related duty" value={dutyId} onChange={e => setDutyId(e.target.value)} className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-white font-mono text-sm" />
          </div>

          <div className="pt-4 flex justify-end gap-3 border-t border-slate-800 mt-6">
            <button type="button" onClick={onClose} className="text-sm text-slate-400 hover:text-white">Cancel</button>
            <button type="submit" disabled={mutation.isPending} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50">
              {mutation.isPending ? 'Saving...' : 'Save Expense'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
