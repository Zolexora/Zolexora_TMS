import { PayablesPage } from './PayablesPage';

export function VendorPaymentHistoryPage() {
  return (
    <div className="space-y-4">
      <div className="rounded-lg bg-indigo-500/10 p-4 border border-indigo-500/20 text-indigo-400 text-sm">
        Viewing unified Vendor Payments & Settlements.
      </div>
      <PayablesPage />
    </div>
  );
}
