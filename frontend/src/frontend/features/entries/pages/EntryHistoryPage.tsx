import React, { useEffect, useState, useCallback } from 'react';
import {
  History, Search, Eye, AlertCircle, Calendar,
  ArrowLeftRight, X
} from 'lucide-react';
import { useCompany } from '../../companies/context/CompanyContext';
import { Table } from '../../../components/Table';
import { Button } from '../../../components/Button';
import { Input } from '../../../components/Input';
import { LoadingState } from '../../../components/LoadingState';
import { ErrorState } from '../../../components/ErrorState';
import { api } from '../../../api/client';
import { ApiError } from '../../../api/errors';
import { useAuth } from '../../auth/hooks/useAuth';

interface LedgerLine {
  account_code: string;
  account_name: string;
  debit: number;
  credit: number;
  description: string | null;
}

interface JournalBatch {
  id: string;
  company_code: string;
  period: string;
  reference: string | null;
  description: string | null;
  status: 'Draft' | 'Posted' | 'Reversed' | string;
  batch_type: string;
  created_by: string | null;
  posted_by: string | null;
  created_at: string;
  posted_at: string | null;
  original_batch_id: string | null;
  reversal_batch_id: string | null;
  debit_total: number;
  credit_total: number;
  lines: LedgerLine[];
}

const STATUS_COLORS: Record<string, string> = {
  Posted: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20',
  Draft: 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20',
  Reversed: 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-400 border-transparent',
};

export const EntryHistoryPage: React.FC = () => {
  const { activeCompany } = useCompany();
  const { can } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBatch, setSelectedBatch] = useState<JournalBatch | null>(null);
  const [batches, setBatches] = useState<JournalBatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reversing, setReversing] = useState(false);

  const loadBatches = useCallback(async () => {
    if (!activeCompany) {
      setBatches([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<JournalBatch[]>(`/entries?company_code=${encodeURIComponent(activeCompany.code)}`);
      setBatches(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to load journal history.');
    } finally {
      setLoading(false);
    }
  }, [activeCompany]);

  useEffect(() => {
    void loadBatches();
  }, [loadBatches]);

  const handleReverse = async (batch: JournalBatch) => {
    if (!window.confirm(`Reverse batch ${batch.reference || batch.id}? This posts an offsetting entry and cannot be undone.`)) {
      return;
    }
    setReversing(true);
    try {
      await api.post(`/entries/${batch.id}/reverse`, {});
      setSelectedBatch(null);
      await loadBatches();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to reverse batch.');
    } finally {
      setReversing(false);
    }
  };

  const filteredBatches = batches.filter(
    (b) =>
      (b.reference || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (b.description || '').toLowerCase().includes(searchTerm.toLowerCase()),
  );

  const columns = [
    {
      key: 'reference',
      header: 'Reference',
      render: (item: JournalBatch) => (
        <span className="font-mono text-xs font-bold text-slate-800 dark:text-slate-200">
          {item.reference || item.id}
        </span>
      ),
    },
    {
      key: 'date',
      header: 'Entry Date',
      render: (item: JournalBatch) => (
        <span className="flex items-center space-x-1.5 text-xs text-slate-500">
          <Calendar className="h-3.5 w-3.5 text-indigo-500" />
          <span>{item.created_at.slice(0, 10)}</span>
        </span>
      ),
    },
    {
      key: 'description',
      header: 'Description',
      render: (item: JournalBatch) => (
        <div className="max-w-xs md:max-w-sm truncate text-slate-700 dark:text-slate-350" title={item.description || ''}>
          {item.description || '—'}
        </div>
      ),
    },
    {
      key: 'debitTotal',
      header: 'Total Value',
      align: 'right' as const,
      render: (item: JournalBatch) => (
        <span className="font-mono font-bold text-slate-800 dark:text-slate-100">
          {item.debit_total.toLocaleString('en-US', { minimumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Ledger Status',
      render: (item: JournalBatch) => (
        <span
          className={`inline-flex px-2.5 py-0.5 rounded-full text-2xs font-bold border ${
            STATUS_COLORS[item.status] || STATUS_COLORS.Draft
          }`}
        >
          {item.status}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Details',
      align: 'right' as const,
      render: (item: JournalBatch) => (
        <button
          onClick={() => setSelectedBatch(item)}
          className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          title="Inspect journal entry"
        >
          <Eye className="h-4 w-4" />
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header Panel */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-slate-100 flex items-center space-x-2">
            <History className="h-7 w-7 text-indigo-500" />
            <span>Journal History</span>
          </h2>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Browse and review posted journal batches and drafts for{' '}
            <span className="font-semibold text-indigo-500">{activeCompany?.name || 'the selected company'}</span>.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-2xl bg-white dark:bg-slate-900/60 border border-slate-200/50 dark:border-slate-850 shadow-sm flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="w-full md:max-w-md">
          <Input
            placeholder="Search by reference or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            leftIcon={<Search className="h-4 w-4 text-slate-400" />}
          />
        </div>
        <div className="flex items-center space-x-2 text-xs text-slate-400 font-medium">
          <AlertCircle className="h-4 w-4 text-indigo-500" />
          <span>Showing {filteredBatches.length} of {batches.length} journal records.</span>
        </div>
      </div>

      {loading && <LoadingState message="Loading journal history..." />}
      {!loading && error && <ErrorState message={error} onRetry={loadBatches} />}
      {!loading && !error && (
        <Table
          columns={columns}
          data={filteredBatches}
          keyExtractor={(item) => item.id}
          emptyMessage="No historical journal entries match your search."
        />
      )}

      {/* Detail Slide-Over Drawer */}
      {selectedBatch && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/60 backdrop-blur-sm animate-fadeIn" role="dialog" aria-modal="true">
          <div className="fixed inset-0" onClick={() => setSelectedBatch(null)}></div>
          <div className="relative w-full max-w-2xl bg-white dark:bg-slate-950 h-full flex flex-col shadow-2xl border-l border-slate-200 dark:border-slate-850 animate-slideLeft">

            {/* Drawer Header */}
            <div className="p-6 border-b border-slate-100 dark:border-slate-850 flex justify-between items-center bg-slate-50/50 dark:bg-slate-900/50">
              <div className="space-y-1">
                <span className="text-2xs font-mono font-bold text-indigo-500 uppercase tracking-widest">Journal Batch details</span>
                <h3 className="text-xl font-extrabold text-slate-800 dark:text-slate-100 flex items-center space-x-2">
                  <span>{selectedBatch.reference || selectedBatch.id}</span>
                  <span
                    className={`inline-flex px-2 py-0.5 rounded-full text-3xs font-bold border ${
                      STATUS_COLORS[selectedBatch.status] || STATUS_COLORS.Draft
                    }`}
                  >
                    {selectedBatch.status}
                  </span>
                </h3>
              </div>
              <button
                onClick={() => setSelectedBatch(null)}
                className="p-2 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Drawer Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">

              {/* Summary details */}
              <div className="grid grid-cols-2 gap-4 bg-slate-50 dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/40 dark:border-slate-800">
                <div>
                  <span className="text-2xs font-bold text-slate-400 uppercase tracking-wide">Post Date</span>
                  <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 mt-0.5">
                    {(selectedBatch.posted_at || selectedBatch.created_at).slice(0, 10)}
                  </p>
                </div>
                <div>
                  <span className="text-2xs font-bold text-slate-400 uppercase tracking-wide">Created By</span>
                  <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 mt-0.5">
                    {selectedBatch.created_by || '—'}
                  </p>
                </div>
                <div className="col-span-2">
                  <span className="text-2xs font-bold text-slate-400 uppercase tracking-wide">Batch Description</span>
                  <p className="text-sm text-slate-700 dark:text-slate-300 mt-0.5 font-medium leading-relaxed">
                    {selectedBatch.description || 'No description provided.'}
                  </p>
                </div>
              </div>

              {/* Ledger Lines */}
              <div className="space-y-3">
                <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center space-x-1.5">
                  <ArrowLeftRight className="h-4 w-4 text-indigo-500" />
                  <span>Ledger Lines</span>
                </h4>
                <div className="rounded-2xl border border-slate-100 dark:border-slate-800 overflow-hidden">
                  <table className="min-w-full text-left">
                    <thead className="bg-slate-50 dark:bg-slate-900 text-2xs font-semibold text-slate-400 uppercase font-mono border-b border-slate-100 dark:border-slate-850">
                      <tr>
                        <th className="py-2.5 px-4">Account</th>
                        <th className="py-2.5 px-4 w-24">Type</th>
                        <th className="py-2.5 px-4 w-32 text-right">Value</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-sm">
                      {selectedBatch.lines.map((line, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/20 dark:hover:bg-slate-900/5">
                          <td className="py-3 px-4">
                            <div className="font-semibold text-slate-700 dark:text-slate-350">{line.account_name}</div>
                            <div className="text-xs text-slate-400 font-mono mt-0.5">
                              {line.account_code}
                              {line.description ? ` · ${line.description}` : ''}
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            <span
                              className={`inline-flex px-1.5 py-0.5 rounded text-3xs font-bold uppercase ${
                                line.debit > 0 ? 'bg-indigo-500/10 text-indigo-500' : 'bg-purple-500/10 text-purple-500'
                              }`}
                            >
                              {line.debit > 0 ? 'Debit' : 'Credit'}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right font-mono font-bold text-slate-800 dark:text-slate-200">
                            {(line.debit || line.credit).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>

            {/* Drawer Footer */}
            <div className="p-6 border-t border-slate-100 dark:border-slate-850 flex justify-end space-x-3 bg-slate-50/50 dark:bg-slate-900/50">
              <Button variant="outline" size="sm" onClick={() => setSelectedBatch(null)}>
                Close Panel
              </Button>
              {selectedBatch.status === 'Posted' && !selectedBatch.reversal_batch_id && can('entry:reverse') && (
                <Button
                  variant="destructive"
                  size="sm"
                  leftIcon={<ArrowLeftRight className="h-4 w-4" />}
                  isLoading={reversing}
                  onClick={() => handleReverse(selectedBatch)}
                >
                  Reverse Batch
                </Button>
              )}
            </div>

          </div>
        </div>
      )}
    </div>
  );
};
