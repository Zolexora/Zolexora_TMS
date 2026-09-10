import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileText, Plus, Search, ShieldCheck } from 'lucide-react';
import { apiClient } from '../../lib/api';

export function RateCardsPage() {
  const [searchTerm, setSearchTerm] = useState('');

  const { data: rateCards, isLoading } = useQuery({
    queryKey: ['rate-cards'],
    queryFn: () => apiClient<any[]>('/api/v1/rate-cards')
  });

  const filteredCards = rateCards?.filter(card => 
    card.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    (card.customer?.name || '').toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Rate Cards & Rules</h1>
          <p className="text-sm text-slate-400">Manage deterministic pricing contracts and operational rules.</p>
        </div>
        <button className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition">
          <Plus className="h-4 w-4" />
          Create Rate Card
        </button>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search by rate card name or customer..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-xl border border-slate-800 bg-slate-950 py-2.5 pl-10 pr-4 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12">
          <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-t-2 border-indigo-500"></div>
        </div>
      ) : filteredCards.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center">
          <div className="rounded-2xl bg-indigo-500/10 p-4 text-indigo-400 mb-4">
            <FileText className="h-8 w-8" />
          </div>
          <h3 className="text-base font-semibold text-white">No rate cards found</h3>
          <p className="mt-1 text-sm text-slate-400 max-w-sm">
            Create a rate card to define automated pricing rules for customer contracts.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredCards.map((card) => (
            <div key={card.id} className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 transition hover:border-slate-700">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-white">{card.name}</h3>
                  <p className="text-xs text-slate-400 mt-1">{card.service_type}</p>
                </div>
                {card.is_active && (
                  <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-400">
                    <ShieldCheck className="h-3 w-3" />
                    Active
                  </span>
                )}
              </div>
              
              <div className="mt-4 pt-4 border-t border-slate-800/80">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-500">Rules</span>
                  <span className="font-medium text-slate-300">{card.rules?.length || 0} configured</span>
                </div>
                <div className="flex items-center justify-between text-sm mt-2">
                  <span className="text-slate-500">Customer</span>
                  <span className="font-medium text-slate-300 truncate max-w-[120px]">
                    {card.customer_id ? 'Contractual' : 'Default/Spot'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
