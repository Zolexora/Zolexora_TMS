import { CreditCard } from 'lucide-react';

export function PaymentsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Cashfree Payments & Collections</h1>
          <p className="text-sm text-slate-400">Payment links, Cashfree webhooks, reconciliations, and ledger status.</p>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-400">
          <CreditCard className="h-3.5 w-3.5" />
          Cashfree Adapter Ready
        </div>
      </div>

      <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center">
        <div className="rounded-2xl bg-indigo-500/10 p-4 text-indigo-400 mb-4">
          <CreditCard className="h-8 w-8" />
        </div>
        <h3 className="text-base font-semibold text-white">No payment transactions recorded</h3>
        <p className="mt-1 text-sm text-slate-400 max-w-sm">
          Cashfree payment links generated for customer invoices will update payment status upon webhook confirmation.
        </p>
      </div>
    </div>
  );
}
