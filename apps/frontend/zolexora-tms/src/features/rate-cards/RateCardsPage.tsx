import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileText, Plus, Search, ShieldCheck, Edit2 } from 'lucide-react';
import { apiClient } from '../../lib/api';
import { RateCardForm } from './RateCardForm';
import { EditRatesModal } from './EditRatesModal';

export function RateCardsPage({ type = 'customer' }: { type?: 'customer' | 'vendor' }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingCard, setEditingCard] = useState<any | null>(null);

  const { data: rateCards, isLoading } = useQuery({
    queryKey: ['rate-cards'],
    queryFn: () => apiClient<any[]>('/api/v1/rate-cards')
  });

  const filteredCards = rateCards?.filter(card => {
    // Filter by type
    if (type === 'customer' && !card.customer_id) return false;
    if (type === 'vendor' && !card.vendor_id) return false;
    
    // Filter by search term
    return card.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
           (card.customer_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
           (card.vendor_name || '').toLowerCase().includes(searchTerm.toLowerCase());
  }) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">
            {type === 'customer' ? 'Customer Rate Cards' : 'Vendor Rate Cards'}
          </h1>
          <p className="text-sm text-slate-400">
            {type === 'customer' ? 'Manage pricing contracts and rules for client billing.' : 'Manage payable rules and contracts for transport vendors.'}
          </p>
        </div>
        <button onClick={() => setIsFormOpen(true)} className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition">
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
            <div key={card.id} className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 transition hover:border-slate-700 flex flex-col justify-between">
              <div>
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-white">{card.name}</h3>
                    <p className="text-xs text-slate-400 mt-1">{card.service_type}</p>
                  </div>
                  {card.is_active && (
                    <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-400 mb-2">
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
                    <span className="text-slate-500">{type === 'customer' ? 'Customer' : 'Vendor'}</span>
                    <span className="font-medium text-slate-300 truncate max-w-[120px]" title={type === 'customer' ? card.customer_name : card.vendor_name}>
                      {type === 'customer' ? (card.customer_name || 'Contractual') : (card.vendor_name || 'Contractual')}
                    </span>
                  </div>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-slate-800/80 flex justify-end">
                <button
                  onClick={() => setEditingCard(card)}
                  className="inline-flex items-center gap-1 text-xs font-medium text-indigo-400 hover:text-indigo-300"
                >
                  <Edit2 className="h-3.5 w-3.5" /> Edit Rates
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
      {isFormOpen && <RateCardForm onClose={() => setIsFormOpen(false)} defaultSide={type === 'customer' ? 'CUSTOMER' : 'VENDOR'} />}
      {editingCard && <EditRatesModal card={editingCard} onClose={() => setEditingCard(null)} />}
    </div>
  );
}
