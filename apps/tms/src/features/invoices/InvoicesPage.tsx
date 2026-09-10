import { FileText, Plus } from 'lucide-react';

export function InvoicesPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Invoicing & Billing</h1>
          <p className="text-sm text-slate-400">Authoritative billing calculation, GST invoices, and credit memos.</p>
        </div>
        <button className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition">
          <Plus className="h-4 w-4" />
          Generate Invoice
        </button>
      </div>

      <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center">
        <div className="rounded-2xl bg-indigo-500/10 p-4 text-indigo-400 mb-4">
          <FileText className="h-8 w-8" />
        </div>
        <h3 className="text-base font-semibold text-white">No invoices issued</h3>
        <p className="mt-1 text-sm text-slate-400 max-w-sm">
          Completed transport duties with finalized odometer and toll charges generate authoritative invoices here.
        </p>
      </div>
    </div>
  );
}
