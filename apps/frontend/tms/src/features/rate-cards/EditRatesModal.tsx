import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { X, CheckCircle2 } from 'lucide-react';
import { apiClient } from '../../lib/api';

export function EditRatesModal({ card, onClose }: { card: any, onClose: () => void }) {
  const queryClient = useQueryClient();
  const [rules, setRules] = useState<any[]>(
    JSON.parse(JSON.stringify(card.rules || []))
  );

  const updateMutation = useMutation({
    mutationFn: async (updatedRules: any[]) => {
      const payload = {
        rules: updatedRules.map((r) => ({
          id: r.id,
          rate: Number(r.rate)
        }))
      };
      return apiClient(`/api/v1/rate-cards/${card.id}/rules`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rate-cards'] });
      onClose();
    }
  });

  const handleRateChange = (id: string, newRate: string) => {
    setRules(rules.map(r => r.id === id ? { ...r, rate: newRate } : r));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-2xl rounded-2xl border border-slate-800 bg-slate-950 shadow-2xl flex flex-col max-h-[85vh]">
        
        <div className="flex items-center justify-between border-b border-slate-800 p-6">
          <div>
            <h2 className="text-xl font-bold text-white">Edit Rates</h2>
            <p className="text-sm text-slate-400">{card.name}</p>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <div className="grid grid-cols-12 gap-4 text-xs font-semibold text-slate-500 mb-2 px-2">
            <div className="col-span-3">Type</div>
            <div className="col-span-6">Parameter / Slab</div>
            <div className="col-span-3 text-right">Rate (₹)</div>
          </div>
          
          {rules.map((rule) => {
            let paramText = rule.parameter;
            try {
              const p = JSON.parse(rule.parameter);
              const parts = [];
              if (p.vehicle_type) parts.push(p.vehicle_type);
              if (p.location) parts.push(p.location);
              if (p.min_km !== undefined) {
                parts.push(`${p.min_km} - ${p.max_km > 9000 ? 'Any' : p.max_km} km`);
              }
              if (parts.length > 0) {
                paramText = parts.join(' | ');
              }
            } catch (e) {}

            return (
              <div key={rule.id} className="grid grid-cols-12 gap-4 items-center rounded-xl border border-slate-800 bg-slate-900/50 p-3">
                <div className="col-span-3 text-sm font-medium text-slate-300">
                  {rule.rule_type.replace('_', ' ')}
                </div>
                <div className="col-span-6 text-sm text-slate-400">
                  {paramText}
                </div>
                <div className="col-span-3">
                  <input
                    type="number"
                    value={rule.rate}
                    onChange={(e) => handleRateChange(rule.id, e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-right text-sm text-white focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>
            );
          })}
        </div>

        <div className="p-6 border-t border-slate-800 bg-slate-900 flex justify-end gap-3 rounded-b-2xl">
          <button type="button" onClick={onClose} className="rounded-lg px-4 py-2 text-sm font-medium text-slate-400 hover:text-white">
            Cancel
          </button>
          <button 
            onClick={() => updateMutation.mutate(rules)}
            disabled={updateMutation.isPending}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-6 py-2 text-sm font-bold text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {updateMutation.isPending ? 'Saving...' : (
              <><CheckCircle2 className="h-4 w-4" /> Save Rates</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
