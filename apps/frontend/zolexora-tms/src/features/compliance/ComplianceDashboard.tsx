import { useState } from 'react';
import { useComplianceRecords, useComplianceRequirements, useVerifyComplianceRecord, useUpdateComplianceRecord } from './hooks';
import { ShieldCheck, ShieldAlert, FileWarning, Clock } from 'lucide-react';
import { ComplianceStatus } from './api';

const formatDate = (dateString: string) => {
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: '2-digit', year: 'numeric' }).format(new Date(dateString));
};

export function ComplianceDashboard() {
  const [statusFilter, setStatusFilter] = useState<ComplianceStatus | 'ALL'>('ALL');
  
  const { data: records = [], isLoading: recordsLoading } = useComplianceRecords(
    statusFilter !== 'ALL' ? { status: statusFilter } : undefined
  );
  const verifyRecord = useVerifyComplianceRecord();
  const updateRecord = useUpdateComplianceRecord();

  const handleExportCSV = () => {
    if (records.length === 0) return;
    const headers = ['Entity', 'Entity ID', 'Requirement', 'Category', 'Status', 'Expiry Date', 'Last Updated'];
    const rows = records.map(record => {
      const req = reqMap.get(record.requirement_id);
      return [
        record.entity_type,
        record.entity_id,
        req?.name || 'Unknown',
        req?.category || 'Unknown',
        record.status,
        record.expiry_date || 'N/A',
        record.updated_at
      ];
    });
    
    const csvContent = [
      headers.join(','),
      ...rows.map(e => e.join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `compliance_report_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  
  const { data: requirements = [] } = useComplianceRequirements();
  
  const reqMap = new Map(requirements.map(r => [r.id, r]));

  const stats = {
    valid: records.filter(r => r.status === 'VALID').length,
    expiring: records.filter(r => r.status === 'EXPIRING_SOON').length,
    missing: records.filter(r => r.status === 'MISSING').length,
    blocked: records.filter(r => ['EXPIRED', 'REJECTED'].includes(r.status) || (r.status === 'MISSING' && reqMap.get(r.requirement_id)?.blocking)).length,
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Compliance Engine Dashboard</h1>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Valid Records */}
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium uppercase tracking-wider text-zinc-500">Valid Records</span>
            <ShieldCheck className="h-5 w-5 text-emerald-500" />
          </div>
          <div className="mt-4">
            <span className="text-3xl font-bold">{stats.valid}</span>
            <p className="mt-1 text-xs text-zinc-500">Currently compliant documents</p>
          </div>
        </div>
        
        {/* Expiring Soon */}
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium uppercase tracking-wider text-zinc-500">Expiring Soon</span>
            <Clock className="h-5 w-5 text-amber-500" />
          </div>
          <div className="mt-4">
            <span className="text-3xl font-bold">{stats.expiring}</span>
            <p className="mt-1 text-xs text-zinc-500">Expiring within 30 days</p>
          </div>
        </div>

        {/* Missing */}
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium uppercase tracking-wider text-zinc-500">Missing</span>
            <FileWarning className="h-5 w-5 text-orange-500" />
          </div>
          <div className="mt-4">
            <span className="text-3xl font-bold">{stats.missing}</span>
            <p className="mt-1 text-xs text-zinc-500">Required but not uploaded</p>
          </div>
        </div>

        {/* Blocked Assets */}
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium uppercase tracking-wider text-zinc-500">Blocked Assets</span>
            <ShieldAlert className="h-5 w-5 text-red-500" />
          </div>
          <div className="mt-4">
            <span className="text-3xl font-bold">{stats.blocked}</span>
            <p className="mt-1 text-xs text-zinc-500">Vehicles/Drivers prevented</p>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm overflow-hidden">
        <div className="p-6 flex flex-row items-center justify-between border-b border-zinc-200 dark:border-zinc-800">
          <div>
            <h3 className="text-lg font-bold">Compliance Records</h3>
            <p className="text-sm text-zinc-500">Overview of all tracked compliance records across the organisation.</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleExportCSV}
              className="inline-flex items-center gap-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-4 py-2 text-sm font-medium hover:bg-zinc-100 dark:hover:bg-zinc-800 transition"
            >
              Export CSV
            </button>
            <div className="w-48">
            <select 
              value={statusFilter} 
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className="flex h-10 w-full rounded-md border border-zinc-300 bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:focus:ring-zinc-400 dark:focus:ring-offset-zinc-900"
            >
              <option value="ALL">All Statuses</option>
              <option value="VALID">Valid</option>
              <option value="EXPIRING_SOON">Expiring Soon</option>
              <option value="EXPIRED">Expired</option>
              <option value="MISSING">Missing</option>
              <option value="VERIFICATION_REQUIRED">Pending Verification</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>
          </div>
        </div>
        <div className="p-0 overflow-x-auto">
          {recordsLoading ? (
            <div className="text-center py-8 text-zinc-500">Loading records...</div>
          ) : (
            <table className="w-full caption-bottom text-sm">
              <thead className="[&_tr]:border-b border-zinc-200 dark:border-zinc-800">
                <tr className="border-b transition-colors hover:bg-zinc-100/50 data-[state=selected]:bg-zinc-100 dark:hover:bg-zinc-800/50 dark:data-[state=selected]:bg-zinc-800">
                  <th className="h-12 px-6 text-left align-middle font-medium text-zinc-500">Entity</th>
                  <th className="h-12 px-6 text-left align-middle font-medium text-zinc-500">Requirement</th>
                  <th className="h-12 px-6 text-left align-middle font-medium text-zinc-500">Status</th>
                  <th className="h-12 px-6 text-left align-middle font-medium text-zinc-500">Expiry Date</th>
                  <th className="h-12 px-6 text-left align-middle font-medium text-zinc-500">Actions</th>
                </tr>
              </thead>
              <tbody className="[&_tr:last-child]:border-0">
                {records.length === 0 ? (
                  <tr className="border-b border-zinc-200 dark:border-zinc-800">
                    <td colSpan={5} className="p-6 text-center text-zinc-500">
                      No compliance records found.
                    </td>
                  </tr>
                ) : (
                  records.map((record) => {
                    const req = reqMap.get(record.requirement_id);
                    return (
                      <tr key={record.id} className="border-b border-zinc-200 dark:border-zinc-800 transition-colors hover:bg-zinc-100/50 dark:hover:bg-zinc-800/50">
                        <td className="p-6 align-middle">
                          <div className="font-medium">{record.entity_type}</div>
                          <div className="text-xs text-zinc-500 font-mono">{record.entity_id.split('-')[0]}...</div>
                        </td>
                        <td className="p-6 align-middle">
                          <div className="font-medium">{req?.name || 'Unknown'}</div>
                          <div className="text-xs text-zinc-500">{req?.category}</div>
                        </td>
                        <td className="p-6 align-middle">
                          <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-zinc-400 focus:ring-offset-2 dark:focus:ring-offset-zinc-900 ${
                            record.status === 'VALID' ? 'border-transparent bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400' :
                            record.status === 'EXPIRING_SOON' ? 'border-transparent bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400' :
                            record.status === 'VERIFICATION_REQUIRED' ? 'text-blue-500 bg-blue-500/10 dark:text-blue-400' :
                            'border-transparent bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                          }`}>
                            {record.status.replace('_', ' ')}
                          </span>
                          {req?.blocking && record.status !== 'VALID' && record.status !== 'EXPIRING_SOON' && (
                            <span className="ml-2 inline-flex items-center rounded-full border-transparent bg-red-100 px-2.5 py-0.5 text-[10px] font-semibold text-red-800 dark:bg-red-900/30 dark:text-red-400">
                              BLOCKING
                            </span>
                          )}
                        </td>
                        <td className="p-6 align-middle">{record.expiry_date ? formatDate(record.expiry_date) : 'N/A'}</td>
                        <td className="p-6 align-middle">
                          <div className="flex items-center gap-2">
                            {record.document_url && (
                              <a
                                href={record.document_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 rounded-lg bg-zinc-100 dark:bg-zinc-800 px-3 py-1.5 text-xs font-medium hover:bg-zinc-200 dark:hover:bg-zinc-700 transition"
                              >
                                View
                              </a>
                            )}
                            {record.status === 'VERIFICATION_REQUIRED' && (
                              <>
                                <button
                                  onClick={() => verifyRecord.mutateAsync({ id: record.id, method: 'MANUAL', comments: 'Looks good' })}
                                  className="inline-flex items-center gap-1 rounded-lg bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-500 hover:bg-emerald-500/20 transition"
                                >
                                  Approve
                                </button>
                                <button
                                  onClick={() => updateRecord.mutateAsync({ ...record, status: 'REJECTED', rejection_reason: 'Invalid document' })}
                                  className="inline-flex items-center gap-1 rounded-lg bg-red-500/10 px-3 py-1.5 text-xs font-medium text-red-500 hover:bg-red-500/20 transition"
                                >
                                  Reject
                                </button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
