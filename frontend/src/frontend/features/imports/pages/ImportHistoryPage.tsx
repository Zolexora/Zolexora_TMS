import React from 'react';
import { 
  History, Download, FileSpreadsheet, Eye, 
  ExternalLink, CheckCircle, AlertCircle 
} from 'lucide-react';
import { useCompany } from '../../companies/context/CompanyContext';
import { Table } from '../../../components/Table';

interface ImportJob {
  id: string;
  filename: string;
  uploadedBy: string;
  uploadedTime: string;
  totalRows: number;
  validRows: number;
  invalidRows: number;
  status: 'Completed' | 'Failed' | 'Pending';
  resultingBatchRef?: string;
}

export const ImportHistoryPage: React.FC = () => {
  const { activeCompany } = useCompany();

  // Mock list of imports
  const mockJobs: ImportJob[] = [
    {
      id: 'job-001',
      filename: 'ara_journal_accruals_jul2026.csv',
      uploadedBy: 'finance_admin@zolexora.com',
      uploadedTime: '2026-07-12 14:30',
      totalRows: 6,
      validRows: 6,
      invalidRows: 0,
      status: 'Completed',
      resultingBatchRef: 'JV-202607-04'
    },
    {
      id: 'job-002',
      filename: 'office_supplies_reimbursement.xlsx',
      uploadedBy: 'entry_clerk@zolexora.com',
      uploadedTime: '2026-07-10 09:15',
      totalRows: 4,
      validRows: 2,
      invalidRows: 2,
      status: 'Failed'
    },
    {
      id: 'job-003',
      filename: 'q2_vehicle_maintenance_records.xlsx',
      uploadedBy: 'fleet_manager@zolexora.com',
      uploadedTime: '2026-07-05 11:22',
      totalRows: 45,
      validRows: 45,
      invalidRows: 0,
      status: 'Completed',
      resultingBatchRef: 'JV-IMP-9860'
    }
  ];

  const columns = [
    {
      key: 'filename',
      header: 'Filename',
      render: (item: ImportJob) => (
        <div className="flex items-center space-x-2">
          <FileSpreadsheet className="h-4.5 w-4.5 text-indigo-500 flex-shrink-0" />
          <span className="font-semibold text-slate-800 dark:text-slate-200 text-xs truncate max-w-xs block">
            {item.filename}
          </span>
        </div>
      )
    },
    { key: 'uploadedTime', header: 'Uploaded Time', className: 'text-xs text-slate-500 font-mono' },
    { key: 'uploadedBy', header: 'Uploaded By', className: 'text-xs text-slate-500' },
    {
      key: 'rows',
      header: 'Rows (Valid/Total)',
      render: (item: ImportJob) => (
        <span className="text-xs font-mono">
          {item.validRows} / {item.totalRows}
        </span>
      )
    },
    {
      key: 'status',
      header: 'Ingestion Status',
      render: (item: ImportJob) => {
        const isCompleted = item.status === 'Completed';
        const isFailed = item.status === 'Failed';
        return (
          <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-2xs font-bold border ${
            isCompleted 
              ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20' 
              : isFailed 
                ? 'bg-red-500/10 text-red-600 border-red-500/20'
                : 'bg-amber-500/10 text-amber-600 border-amber-500/20'
          }`}>
            {isCompleted ? <CheckCircle className="h-3 w-3" /> : <AlertCircle className="h-3 w-3" />}
            <span>{item.status}</span>
          </span>
        );
      }
    },
    {
      key: 'resultingBatchRef',
      header: 'Linked Journal',
      render: (item: ImportJob) => item.resultingBatchRef ? (
        <button className="inline-flex items-center space-x-1 text-indigo-500 hover:underline text-xs font-bold font-mono">
          <span>{item.resultingBatchRef}</span>
          <ExternalLink className="h-3 w-3" />
        </button>
      ) : (
        <span className="text-slate-400 text-xs">-</span>
      )
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right' as const,
      render: () => (
        <div className="flex justify-end space-x-2">
          <button className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-500 hover:bg-slate-50 dark:hover:bg-slate-800 transition">
            <Download className="h-4 w-4" />
          </button>
          <button className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-500 hover:bg-slate-50 dark:hover:bg-slate-800 transition">
            <Eye className="h-4 w-4" />
          </button>
        </div>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header Panel */}
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-slate-100 flex items-center space-x-2">
          <History className="h-7 w-7 text-indigo-500" />
          <span>Import History Logs</span>
        </h2>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Review bulk data ingestion files and background parser logs for <span className="font-semibold text-indigo-500">{activeCompany?.name || 'All Companies'}</span>.
        </p>
      </div>

      {/* Main Table */}
      <Table 
        columns={columns}
        data={mockJobs}
        keyExtractor={(item) => item.id}
        emptyMessage="No import logs found for this scope."
      />
    </div>
  );
};
