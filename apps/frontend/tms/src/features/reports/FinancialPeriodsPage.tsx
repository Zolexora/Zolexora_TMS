import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Calendar, Lock, Unlock, Plus } from 'lucide-react';
import { apiClient } from '../../lib/api';

export function FinancialPeriodsPage() {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [month, setMonth] = useState('');
  const [year, setYear] = useState('');

  const { data: periods, isLoading } = useQuery({
    queryKey: ['financial-periods'],
    queryFn: () => apiClient<any[]>('/api/v1/pl/periods')
  });

  const createMutation = useMutation({
    mutationFn: () => apiClient('/api/v1/pl/periods', {
      method: 'POST',
      body: JSON.stringify({ month: parseInt(month), year: parseInt(year) })
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['financial-periods'] });
      setModalOpen(false);
      setMonth('');
      setYear('');
    }
  });

  const closeMutation = useMutation({
    mutationFn: (id: string) => apiClient(`/api/v1/pl/periods/${id}/close`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['financial-periods'] });
      queryClient.invalidateQueries({ queryKey: ['pnl'] });
      alert('Period closed. Financial records in this period are now locked.');
    }
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Financial Periods</h1>
          <p className="text-sm text-slate-400">Manage financial reporting periods (Open/Close).</p>
        </div>
        <button 
          onClick={() => setModalOpen(true)}
          className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 transition"
        >
          <Plus className="h-4 w-4" />
          Open New Period
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12">
          <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-t-2 border-indigo-500"></div>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-800 bg-slate-900/80 text-slate-400">
              <tr>
                <th className="p-4 font-medium">Period</th>
                <th className="p-4 font-medium">Status</th>
                <th className="p-4 font-medium">Opened At</th>
                <th className="p-4 font-medium">Closed At</th>
                <th className="p-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {periods?.map(p => (
                <tr key={p.id} className="hover:bg-slate-800/30 transition">
                  <td className="p-4 text-white font-medium flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-slate-500" />
                    {p.month}/{p.year}
                  </td>
                  <td className="p-4">
                    {p.status === 'OPEN' ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-400">
                        <Unlock className="h-3 w-3" /> OPEN
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full bg-red-500/10 px-2 py-0.5 text-xs font-medium text-red-400">
                        <Lock className="h-3 w-3" /> CLOSED
                      </span>
                    )}
                  </td>
                  <td className="p-4 text-slate-400">{new Date(p.created_at).toLocaleDateString()}</td>
                  <td className="p-4 text-slate-400">{p.closed_at ? new Date(p.closed_at).toLocaleDateString() : '-'}</td>
                  <td className="p-4 text-right">
                    {p.status === 'OPEN' && (
                      <button 
                        onClick={() => {
                          if (confirm(`Are you sure you want to close ${p.month}/${p.year}? This action cannot be reversed and will lock related financial records.`)) {
                            closeMutation.mutate(p.id);
                          }
                        }}
                        disabled={closeMutation.isPending}
                        className="rounded-md bg-red-600/20 px-3 py-1.5 text-xs font-medium text-red-400 hover:bg-red-600/30"
                      >
                        Close Period
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-white">Open Financial Period</h2>
            <div className="mt-4 space-y-4">
              <div>
                <label className="mb-1 block text-sm text-slate-300">Month (1-12)</label>
                <input type="number" min="1" max="12" value={month} onChange={e => setMonth(e.target.value)} className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-white" />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-300">Year</label>
                <input type="number" min="2020" max="2100" value={year} onChange={e => setYear(e.target.value)} className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-white" />
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button onClick={() => setModalOpen(false)} className="rounded-lg px-4 py-2 text-sm text-slate-300 hover:bg-slate-800">Cancel</button>
              <button onClick={() => createMutation.mutate()} disabled={createMutation.isPending || !month || !year} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-500">Open</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
