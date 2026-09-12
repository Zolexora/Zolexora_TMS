import re

with open("apps/tms/src/features/billing/BillingPage.tsx", "r") as f:
    content = f.read()

imports = """
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { FileText, CheckCircle2 } from 'lucide-react';
import { apiClient } from '../../lib/api';
"""
content = re.sub(r"import .*? from '../../lib/api';", imports, content, flags=re.DOTALL)

state_and_mut = """
export function BillingPage() {
  const queryClient = useQueryClient();
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const { data: billingRecords, isLoading } = useQuery({
    queryKey: ['billing'],
    queryFn: () => apiClient<any[]>('/api/v1/billing')
  });

  const generateMutation = useMutation({
    mutationFn: (ids: string[]) => apiClient('/api/v1/invoices', {
      method: 'POST',
      body: JSON.stringify({ billing_record_ids: ids })
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['billing'] });
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      setSelectedIds([]);
      alert('Invoice created successfully!');
    }
  });

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setSelectedIds((billingRecords || []).filter(r => r.status === 'PENDING').map(r => r.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelect = (id: string) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
  };
"""

content = re.sub(r"export function BillingPage\(\) \{.*?\}\);", state_and_mut, content, flags=re.DOTALL)

header = """      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Billing Pipelines</h1>
          <p className="text-sm text-slate-400">View pending financial snapshots ready to be consolidated into invoices.</p>
        </div>
        <button
          onClick={() => generateMutation.mutateAsync(selectedIds)}
          disabled={selectedIds.length === 0 || generateMutation.isPending}
          className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition disabled:opacity-50"
        >
          {generateMutation.isPending ? 'Generating...' : `Generate Invoice (${selectedIds.length})`}
        </button>
      </div>"""

content = re.sub(r"<div className=\"flex items-center justify-between\">.*?</div>\s*</div>", header, content, flags=re.DOTALL)

# Now to fix the table mapping
# I don't know the exact current mapping, let me just replace the return block for the data with a new table.
