import { PayablesPage } from './PayablesPage';

export function VendorSettlementsPage() {
  return (
    <div className="space-y-4">
      <div className="rounded-lg bg-amber-500/10 p-4 border border-amber-500/20 text-amber-400 text-sm">
        Viewing unified DCO & Vendor Settlements.
      </div>
      <PayablesPage />
    </div>
  );
}
