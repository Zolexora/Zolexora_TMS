import React, { useState } from 'react';
import { 
  ShieldAlert, Search, Eye, X, 
  Terminal, ShieldCheck, User, Calendar, Database 
} from 'lucide-react';
import { useCompany } from '../../companies/context/CompanyContext';
import { Table } from '../../../components/Table';
import { Button } from '../../../components/Button';
import { Input } from '../../../components/Input';

interface AuditRecord {
  id: string;
  timestamp: string;
  user: string;
  action: string;
  entityType: string;
  entityName: string;
  requestId: string;
  summary: string;
  details: {
    before?: Record<string, any>;
    after?: Record<string, any>;
    ipAddress: string;
    userAgent: string;
  };
}

export const AuditLogsPage: React.FC = () => {
  const { activeCompany } = useCompany();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRecord, setSelectedRecord] = useState<AuditRecord | null>(null);

  // Mock audit records
  const mockRecords: AuditRecord[] = [
    {
      id: 'aud-001',
      timestamp: '2026-07-12 14:31:05',
      user: 'finance_admin@zolexora.com',
      action: 'POST_BATCH',
      entityType: 'entry_batches',
      entityName: 'JV-202607-04',
      requestId: 'req-f8d9b1c2e3',
      summary: 'Posted manual journal entry batch JV-202607-04 ($45,000.00)',
      details: {
        before: { status: 'Draft' },
        after: { status: 'Posted', postedAt: '2026-07-12T14:31:05Z' },
        ipAddress: '192.168.1.105',
        userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
      }
    },
    {
      id: 'aud-002',
      timestamp: '2026-07-12 14:28:44',
      user: 'finance_admin@zolexora.com',
      action: 'CONFIRM_IMPORT',
      entityType: 'import_jobs',
      entityName: 'job-001',
      requestId: 'req-a1b2c3d4e5',
      summary: 'Confirmed and parsed CSV import job for ARAVALI (6 rows)',
      details: {
        before: { status: 'Pending_Review' },
        after: { status: 'Completed', processedRows: 6 },
        ipAddress: '192.168.1.105',
        userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
      }
    },
    {
      id: 'aud-003',
      timestamp: '2026-07-10 11:00:21',
      user: 'admin_sys@zolexora.com',
      action: 'LOCK_PERIOD',
      entityType: 'periods',
      entityName: 'ARAVALI-2026-06',
      requestId: 'req-7c8d9e0f1a',
      summary: 'Locked fiscal period ARAVALI-2026-06 to prevent modifications',
      details: {
        before: { isLocked: false },
        after: { isLocked: true },
        ipAddress: '10.0.4.52',
        userAgent: 'Cloudflare-Worker'
      }
    }
  ];

  const filteredRecords = mockRecords.filter(r => 
    r.user.toLowerCase().includes(searchTerm.toLowerCase()) || 
    r.summary.toLowerCase().includes(searchTerm.toLowerCase()) || 
    r.requestId.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const columns = [
    { key: 'timestamp', header: 'Timestamp', className: 'text-xs text-slate-500 font-mono w-48' },
    { key: 'user', header: 'User', className: 'text-xs text-slate-700 font-semibold' },
    { 
      key: 'action', 
      header: 'Action',
      render: (item: AuditRecord) => (
        <span className="font-mono text-xs font-bold text-slate-800 bg-slate-100 dark:bg-slate-800 dark:text-slate-200 px-2 py-0.5 rounded">
          {item.action}
        </span>
      )
    },
    { key: 'summary', header: 'Event Summary', className: 'text-xs text-slate-500 max-w-sm truncate' },
    { key: 'requestId', header: 'Request ID', className: 'text-xs font-mono text-slate-400' },
    {
      key: 'actions',
      header: 'Inspect',
      align: 'right' as const,
      render: (item: AuditRecord) => (
        <button
          onClick={() => setSelectedRecord(item)}
          className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
        >
          <Eye className="h-4 w-4" />
        </button>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header Panel */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-slate-100 flex items-center space-x-2">
            <ShieldAlert className="h-7 w-7 text-indigo-500" />
            <span>Audit Logs Trail</span>
          </h2>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Track security events, data operations, and period modifications for <span className="font-semibold text-indigo-500">{activeCompany?.name || 'All Companies'}</span>.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="p-4 bg-white dark:bg-slate-900/60 border border-slate-200/50 dark:border-slate-850 rounded-2xl flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="w-full md:max-w-md">
          <Input 
            placeholder="Search by user email, action, request ID..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            leftIcon={<Search className="h-4 w-4 text-slate-400" />}
          />
        </div>
        <div className="flex items-center space-x-2 text-xs text-slate-400 font-semibold">
          <ShieldCheck className="h-4 w-4 text-emerald-500" />
          <span>Integrity Logs Active</span>
        </div>
      </div>

      {/* Table Section */}
      <Table 
        columns={columns}
        data={filteredRecords}
        keyExtractor={(item) => item.id}
        emptyMessage="No security events match search criteria."
      />

      {/* Detail Slide-Over Drawer */}
      {selectedRecord && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/60 backdrop-blur-sm animate-fadeIn" role="dialog" aria-modal="true">
          <div className="fixed inset-0" onClick={() => setSelectedRecord(null)}></div>
          <div className="relative w-full max-w-2xl bg-white dark:bg-slate-950 h-full flex flex-col shadow-2xl border-l border-slate-200 dark:border-slate-850 animate-slideLeft">
            
            {/* Header */}
            <div className="p-6 border-b border-slate-100 dark:border-slate-850 flex justify-between items-center bg-slate-50/50 dark:bg-slate-900/50">
              <div className="space-y-1">
                <span className="text-2xs font-mono font-bold text-indigo-500 uppercase tracking-widest">Audit Event Details</span>
                <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">
                  {selectedRecord.action} - {selectedRecord.entityName}
                </h3>
              </div>
              <button 
                onClick={() => setSelectedRecord(null)} 
                className="p-2 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              
              {/* Metadata */}
              <div className="grid grid-cols-2 gap-4 bg-slate-50 dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/40 dark:border-slate-800">
                <div className="flex items-center space-x-2.5">
                  <User className="h-5 w-5 text-indigo-500" />
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase block">Actor</span>
                    <span className="text-xs font-semibold text-slate-800 dark:text-slate-100">{selectedRecord.user}</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2.5">
                  <Calendar className="h-5 w-5 text-indigo-500" />
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase block">Timestamp</span>
                    <span className="text-xs font-semibold text-slate-800 dark:text-slate-100">{selectedRecord.timestamp}</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2.5">
                  <Database className="h-5 w-5 text-indigo-500" />
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase block">Target Entity</span>
                    <span className="text-xs font-mono font-semibold text-slate-800 dark:text-slate-100">{selectedRecord.entityType} ({selectedRecord.entityName})</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2.5">
                  <Terminal className="h-5 w-5 text-indigo-500" />
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase block">Request ID</span>
                    <span className="text-xs font-mono font-semibold text-slate-800 dark:text-slate-100">{selectedRecord.requestId}</span>
                  </div>
                </div>
              </div>

              {/* Event Summary */}
              <div className="space-y-1">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wide">Event Summary</span>
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 leading-relaxed bg-slate-50 dark:bg-slate-900 p-4 rounded-xl border border-slate-200/30">
                  {selectedRecord.summary}
                </p>
              </div>

              {/* State Diff */}
              <div className="space-y-3">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wide">State Modifications</span>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase block">Before</span>
                    <pre className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200/50 dark:border-slate-800 font-mono text-xs text-slate-600 dark:text-slate-400 overflow-x-auto">
                      {JSON.stringify(selectedRecord.details.before || null, null, 2)}
                    </pre>
                  </div>
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase block text-indigo-500">After</span>
                    <pre className="p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/10 font-mono text-xs text-indigo-600 dark:text-indigo-400 overflow-x-auto">
                      {JSON.stringify(selectedRecord.details.after || null, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>

            </div>

            {/* Footer */}
            <div className="p-6 border-t border-slate-100 dark:border-slate-850 flex justify-end bg-slate-50/50 dark:bg-slate-900/50">
              <Button variant="outline" size="sm" onClick={() => setSelectedRecord(null)}>
                Close Panel
              </Button>
            </div>

          </div>
        </div>
      )}
    </div>
  );
};
