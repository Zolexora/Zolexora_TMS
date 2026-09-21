import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Receipt, Plus, IndianRupee } from 'lucide-react';
import { apiClient } from '../../lib/api';
import { ExpenseForm } from './ExpenseForm';

export function ExpensesPage() {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const { data: expenses, isLoading } = useQuery({
    queryKey: ['expenses'],
    queryFn: () => apiClient<any[]>('/api/v1/expenses')
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Expenses</h1>
          <p className="text-sm text-slate-400">Log operational costs like fuel, tolls, and maintenance.</p>
        </div>
        <button 
          onClick={() => setIsFormOpen(true)}
          className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition"
        >
          <Plus className="h-4 w-4" />
          Log Expense
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12">
          <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-t-2 border-indigo-500"></div>
        </div>
      ) : expenses?.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center">
          <div className="rounded-2xl bg-indigo-500/10 p-4 text-indigo-400 mb-4">
            <Receipt className="h-8 w-8" />
          </div>
          <h3 className="text-base font-semibold text-white">No expenses recorded</h3>
          <p className="mt-1 text-sm text-slate-400 max-w-sm">
            Log your first operational expense to track profitability accurately.
          </p>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-800 bg-slate-900/80 text-slate-400">
              <tr>
                <th className="p-4 font-medium">Date</th>
                <th className="p-4 font-medium">Category</th>
                <th className="p-4 font-medium">Description</th>
                <th className="p-4 font-medium">Duty ID</th>
                <th className="p-4 font-medium text-right">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {expenses?.map(exp => (
                <tr key={exp.id} className="hover:bg-slate-800/30 transition">
                  <td className="p-4 text-slate-300 font-medium">{new Date(exp.incurred_date || exp.created_at).toLocaleDateString()}</td>
                  <td className="p-4">
                    <span className="inline-flex items-center rounded-full bg-slate-800 px-2 py-0.5 text-xs font-medium text-slate-300">
                      {exp.category}
                    </span>
                  </td>
                  <td className="p-4 text-slate-400">{exp.description}</td>
                  <td className="p-4 text-slate-400 font-mono text-xs">{exp.duty_id ? exp.duty_id.split('-')[0] : '-'}</td>
                  <td className="p-4 text-white font-semibold text-right">
                    <IndianRupee className="inline h-3 w-3 text-slate-500"/> {exp.amount}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      {isFormOpen && <ExpenseForm onClose={() => setIsFormOpen(false)} />}
    </div>
  );
}
