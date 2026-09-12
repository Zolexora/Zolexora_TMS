
import { useQuery,  } from '@tanstack/react-query';
import { CreditCard,IndianRupee } from 'lucide-react';
import { apiClient } from '../../lib/api';

export function PaymentsPage() {
  
  const { data: payments, isLoading } = useQuery({
    queryKey: ['payments'],
    queryFn: () => apiClient<any[]>('/api/v1/payments')
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Customer Payments</h1>
          <p className="text-sm text-slate-400">Record incoming payments and allocate them to invoices.</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12">
          <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-t-2 border-indigo-500"></div>
        </div>
      ) : payments?.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center">
          <div className="rounded-2xl bg-indigo-500/10 p-4 text-indigo-400 mb-4">
            <CreditCard className="h-8 w-8" />
          </div>
          <h3 className="text-base font-semibold text-white">No payments recorded</h3>
          <p className="mt-1 text-sm text-slate-400 max-w-sm">
            Record a payment to mark an invoice as paid.
          </p>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-800 bg-slate-900/80 text-slate-400">
              <tr>
                <th className="p-4 font-medium">Date</th>
                <th className="p-4 font-medium">Customer</th>
                <th className="p-4 font-medium">Reference</th>
                <th className="p-4 font-medium">Method</th>
                <th className="p-4 font-medium text-right">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {payments?.map(payment => (
                <tr key={payment.id} className="hover:bg-slate-800/30 transition">
                  <td className="p-4 text-slate-300 font-medium">{new Date(payment.payment_date || payment.created_at).toLocaleDateString()}</td>
                  <td className="p-4 text-slate-300 font-medium">{payment.customer_name || 'Customer'}</td>
                  <td className="p-4 text-slate-400">{payment.reference_number || '-'}</td>
                  <td className="p-4">
                    <span className="inline-flex items-center rounded-full bg-slate-800 px-2 py-0.5 text-xs font-medium text-slate-300">
                      {payment.payment_method}
                    </span>
                  </td>
                  <td className="p-4 text-emerald-400 font-semibold text-right">
                    + <IndianRupee className="inline h-3 w-3 text-emerald-500"/> {payment.amount}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
