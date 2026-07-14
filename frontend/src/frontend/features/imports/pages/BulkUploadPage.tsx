import React, { useState } from 'react';
import { 
  UploadCloud, FileSpreadsheet, CheckCircle2, AlertOctagon, 
  ArrowRight, Download, Search, ChevronRight 
} from 'lucide-react';
import { useCompany } from '../../companies/context/CompanyContext';
import { Button } from '../../../components/Button';
import { Table } from '../../../components/Table';
import { Input } from '../../../components/Input';

interface ParsedRow {
  rowNum: number;
  company: string;
  year: number;
  month: string;
  accountCode: string;
  amount: number;
  direction: 'Debit' | 'Credit';
  status: 'Valid' | 'Invalid';
  error?: string;
}

export const BulkUploadPage: React.FC = () => {
  const { activeCompany } = useCompany();
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileSize, setFileSize] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<'All' | 'Valid' | 'Invalid'>('All');
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Stepper names
  const steps = [
    { num: 1, name: 'Select File' },
    { num: 2, name: 'Parse & Validate' },
    { num: 3, name: 'Review & Confirm' },
    { num: 4, name: 'Complete' }
  ];

  // Mock parsed and validated rows (from a monthly entry import)
  const mockRows: ParsedRow[] = [
    { rowNum: 1, company: 'ARAVALI', year: 2026, month: '07', accountCode: 'REV-101', amount: 45000, direction: 'Credit', status: 'Valid' },
    { rowNum: 2, company: 'ARAVALI', year: 2026, month: '07', accountCode: 'ACC-110', amount: 45000, direction: 'Debit', status: 'Valid' },
    { rowNum: 3, company: 'ARAVALI', year: 2026, month: '07', accountCode: 'EXP-909', amount: 3500, direction: 'Debit', status: 'Invalid', error: 'Account code EXP-909 does not exist for company ARAVALI.' },
    { rowNum: 4, company: 'ARAVALI', year: 2026, month: '07', accountCode: 'EXP-202', amount: 12000, direction: 'Debit', status: 'Valid' },
    { rowNum: 5, company: 'ARAVALI', year: 2026, month: '07', accountCode: 'ACC-102', amount: 15500, direction: 'Credit', status: 'Valid' },
    { rowNum: 6, company: 'ARAVALI', year: 2026, month: '07', accountCode: 'EXP-201', amount: -250, direction: 'Debit', status: 'Invalid', error: 'Negative amounts are rejected in accounting ledger lines.' }
  ];

  // Filters
  const filteredRows = mockRows.filter(row => {
    const matchesSearch = row.accountCode.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          (row.error && row.error.toLowerCase().includes(searchTerm.toLowerCase()));
    
    if (filterStatus === 'Valid') return row.status === 'Valid' && matchesSearch;
    if (filterStatus === 'Invalid') return row.status === 'Invalid' && matchesSearch;
    return matchesSearch;
  });

  const totalRows = mockRows.length;
  const invalidRows = mockRows.filter(r => r.status === 'Invalid').length;
  const validRows = totalRows - invalidRows;

  // Row Preview Columns
  const columns = [
    { key: 'rowNum', header: 'Row #', align: 'center' as const, className: 'w-16 font-mono text-xs text-slate-400' },
    { key: 'company', header: 'Company', className: 'font-semibold text-xs' },
    { key: 'period', header: 'Period', render: (row: ParsedRow) => `${row.year}-${row.month}`, className: 'font-mono text-xs text-slate-500' },
    { key: 'accountCode', header: 'Account Code', className: 'font-mono text-xs font-bold text-slate-700 dark:text-slate-300' },
    { key: 'direction', header: 'Type', render: (row: ParsedRow) => (
      <span className={`inline-flex px-1.5 py-0.5 rounded text-3xs font-bold uppercase ${
        row.direction === 'Debit' ? 'bg-indigo-500/10 text-indigo-500' : 'bg-purple-500/10 text-purple-500'
      }`}>
        {row.direction}
      </span>
    )},
    { key: 'amount', header: 'Amount ($)', align: 'right' as const, render: (row: ParsedRow) => (
      <span className="font-mono font-bold">${row.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
    )},
    { key: 'status', header: 'Status', render: (row: ParsedRow) => (
      <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-2xs font-bold border ${
        row.status === 'Valid' 
          ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20' 
          : 'bg-red-500/10 text-red-600 border-red-500/20'
      }`}>
        <span>{row.status}</span>
      </span>
    )},
    { key: 'error', header: 'Validation Notes', className: 'text-xs text-red-500 dark:text-red-400 max-w-xs truncate' }
  ];

  // Actions
  const handleSelectMockFile = (type: 'csv' | 'xlsx') => {
    setIsLoading(true);
    setTimeout(() => {
      setFileName(type === 'csv' ? 'monthly_journal_accruals.csv' : 'q2_operational_records.xlsx');
      setFileSize('14.2 KB');
      setCurrentStep(2);
      setIsLoading(false);
    }, 800);
  };

  const handleNextStep = () => {
    if (currentStep === 2) {
      setCurrentStep(3);
    } else if (currentStep === 3) {
      setIsLoading(true);
      setTimeout(() => {
        setCurrentStep(4);
        setIsLoading(false);
      }, 1000);
    }
  };

  const handleReset = () => {
    setFileName(null);
    setFileSize(null);
    setCurrentStep(1);
    setFilterStatus('All');
  };

  return (
    <div className="space-y-6">
      {/* Header Panel */}
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-slate-100">
          Bulk Import Ledger
        </h2>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Perform multi-row financial ingestion for <span className="font-semibold text-indigo-500">{activeCompany?.name || 'All Companies'}</span>.
        </p>
      </div>

      {/* Stepper Progress Bar */}
      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900/60 border border-slate-200/50 dark:border-slate-850 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        {steps.map((st, idx) => {
          const isCompleted = currentStep > st.num;
          const isActive = currentStep === st.num;
          
          return (
            <React.Fragment key={st.num}>
              <div className="flex items-center space-x-3 flex-1">
                <span className={`h-8 w-8 rounded-xl flex items-center justify-center text-xs font-bold border transition-colors ${
                  isCompleted 
                    ? 'bg-emerald-500 border-emerald-500 text-white shadow-md shadow-emerald-500/10' 
                    : isActive 
                      ? 'bg-indigo-600 border-indigo-600 text-white shadow-md shadow-indigo-500/10' 
                      : 'bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-400'
                }`}>
                  {isCompleted ? '✓' : st.num}
                </span>
                <span className={`text-sm font-semibold ${
                  isActive ? 'text-indigo-600 dark:text-indigo-400 font-bold' : 'text-slate-500'
                }`}>
                  {st.name}
                </span>
              </div>
              {idx < steps.length - 1 && (
                <ChevronRight className="hidden md:block h-4 w-4 text-slate-300 dark:text-slate-700" />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* STEP 1: SELECT FILE */}
      {currentStep === 1 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 p-10 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/40 flex flex-col items-center justify-center text-center space-y-4">
            <div className="p-4 bg-indigo-500/5 rounded-2xl text-indigo-500">
              <UploadCloud className="h-10 w-10 animate-bounce" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">Drag and drop file here</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Supports standard CSV or XLSX formatting templates, up to 10MB.</p>
            </div>
            <div className="flex items-center space-x-3 pt-2">
              <Button 
                variant="outline" 
                size="sm" 
                leftIcon={<FileSpreadsheet className="h-4 w-4 text-emerald-500" />}
                onClick={() => handleSelectMockFile('csv')}
                isLoading={isLoading}
              >
                Upload mock CSV
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                leftIcon={<FileSpreadsheet className="h-4 w-4 text-emerald-500" />}
                onClick={() => handleSelectMockFile('xlsx')}
                isLoading={isLoading}
              >
                Upload mock XLSX
              </Button>
            </div>
          </div>

          {/* Guidelines Sidebar */}
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900/60 border border-slate-200/50 dark:border-slate-850 shadow-sm space-y-4">
            <h4 className="text-sm font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide">Import Instructions</h4>
            <ul className="text-xs text-slate-500 dark:text-slate-400 space-y-2.5 list-disc pl-4 leading-relaxed">
              <li>Values must represent minor units (integers) to prevent floating-point discrepancies.</li>
              <li>Columns must include: <code className="font-mono text-indigo-500">company_code</code>, <code className="font-mono text-indigo-500">year</code>, <code className="font-mono text-indigo-500">month</code>, <code className="font-mono text-indigo-500">account_code</code>, <code className="font-mono text-indigo-500">direction</code>, <code className="font-mono text-indigo-500">amount</code>.</li>
              <li>All targeted company periods must be unlocked and active.</li>
            </ul>
            <Button variant="secondary" className="w-full text-center" leftIcon={<Download className="h-4 w-4" />}>
              Download CSV Template
            </Button>
          </div>
        </div>
      )}

      {/* STEP 2: PARSE & VALIDATE */}
      {currentStep === 2 && (
        <div className="space-y-6">
          {/* File Selected Badge */}
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-850 flex justify-between items-center text-sm font-semibold">
            <div className="flex items-center space-x-2.5">
              <FileSpreadsheet className="h-5 w-5 text-emerald-500" />
              <span className="text-slate-700 dark:text-slate-350">{fileName}</span>
              <span className="text-xs text-slate-400 font-mono">({fileSize})</span>
            </div>
            <button onClick={handleReset} className="text-xs font-bold text-slate-400 hover:text-red-500 underline">Remove file</button>
          </div>

          {/* Validation Metrics Summary */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="p-5 bg-white dark:bg-slate-900/60 border border-slate-200/50 dark:border-slate-850 rounded-2xl shadow-sm">
              <span className="text-xs font-bold text-slate-400 uppercase">Total Imported Rows</span>
              <h4 className="text-2xl font-black text-slate-800 dark:text-slate-100 mt-1 font-mono">{totalRows}</h4>
            </div>
            <div className="p-5 bg-emerald-500/5 border border-emerald-500/20 rounded-2xl shadow-sm">
              <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase">Valid Rows</span>
              <h4 className="text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1 font-mono">{validRows}</h4>
            </div>
            <div className="p-5 bg-red-500/5 border border-red-500/20 rounded-2xl shadow-sm">
              <span className="text-xs font-bold text-red-600 dark:text-red-400 uppercase">Invalid Rows</span>
              <h4 className="text-2xl font-black text-red-600 dark:text-red-400 mt-1 font-mono">{invalidRows}</h4>
            </div>
            <div className="p-5 bg-amber-500/5 border border-amber-500/20 rounded-2xl shadow-sm">
              <span className="text-xs font-bold text-amber-600 dark:text-amber-400 uppercase font-semibold">Validation Warnings</span>
              <h4 className="text-2xl font-black text-amber-600 dark:text-amber-400 mt-1 font-mono">0</h4>
            </div>
          </div>

          {/* Preview Filters & Search */}
          <div className="p-4 bg-white dark:bg-slate-900/60 border border-slate-200/50 dark:border-slate-850 rounded-2xl flex flex-col sm:flex-row justify-between items-center gap-4">
            <div className="flex items-center space-x-2">
              <button 
                onClick={() => setFilterStatus('All')}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition ${
                  filterStatus === 'All' ? 'bg-indigo-500 text-white border-indigo-500' : 'bg-transparent text-slate-500 border-slate-200 dark:border-slate-800'
                }`}
              >
                All Rows ({totalRows})
              </button>
              <button 
                onClick={() => setFilterStatus('Valid')}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition ${
                  filterStatus === 'Valid' ? 'bg-emerald-500 text-white border-emerald-500' : 'bg-transparent text-slate-500 border-slate-200 dark:border-slate-800'
                }`}
              >
                Valid Only ({validRows})
              </button>
              <button 
                onClick={() => setFilterStatus('Invalid')}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition ${
                  filterStatus === 'Invalid' ? 'bg-red-500 text-white border-red-500' : 'bg-transparent text-slate-500 border-slate-200 dark:border-slate-800'
                }`}
              >
                Invalid Only ({invalidRows})
              </button>
            </div>

            <div className="w-full sm:max-w-xs">
              <Input 
                placeholder="Search account code..." 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                leftIcon={<Search className="h-4 w-4 text-slate-400" />}
              />
            </div>
          </div>

          {/* Preview Table */}
          <Table 
            columns={columns}
            data={filteredRows}
            keyExtractor={(item) => item.rowNum}
            emptyMessage="No parsed rows match selected validation filter."
          />

          {/* Errors Download & Stepper Controls */}
          <div className="flex justify-between items-center bg-slate-50/50 dark:bg-slate-900/50 p-5 rounded-2xl border border-slate-200/50 dark:border-slate-850">
            {invalidRows > 0 ? (
              <Button variant="outline" size="sm" className="border-red-200 hover:bg-red-500/10 text-red-600 dark:text-red-400" leftIcon={<Download className="h-4 w-4" />}>
                Export Error CSV ({invalidRows} Rows)
              </Button>
            ) : <div />}

            <div className="flex space-x-3">
              <Button variant="secondary" size="sm" onClick={handleReset}>Cancel</Button>
              <Button 
                variant="primary" 
                size="sm" 
                rightIcon={<ArrowRight className="h-4 w-4" />}
                onClick={handleNextStep}
                disabled={invalidRows > 0}
                title={invalidRows > 0 ? 'Resolve validation issues first to proceed' : ''}
              >
                Next Step
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* STEP 3: REVIEW & CONFIRM */}
      {currentStep === 3 && (
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900/60 border border-slate-200/50 dark:border-slate-850 shadow-sm space-y-6">
          <div className="space-y-2">
            <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center space-x-2">
              <AlertOctagon className="h-5 w-5 text-indigo-500" />
              <span>Review Batch Summary before Posting</span>
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-xl leading-relaxed">
              Confirming imports will generate a posted ledger batch. Please verify totals and account assignments.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-5 bg-slate-50 dark:bg-slate-900 border border-slate-200/40 dark:border-slate-800 rounded-xl">
            <div>
              <span className="text-2xs font-bold text-slate-400 uppercase tracking-wide">Target Company</span>
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 mt-0.5">{activeCompany?.name || 'ARAVALI'}</p>
            </div>
            <div>
              <span className="text-2xs font-bold text-slate-400 uppercase tracking-wide">Target Period</span>
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 mt-0.5">2026-07</p>
            </div>
            <div>
              <span className="text-2xs font-bold text-slate-400 uppercase tracking-wide">Debits Total</span>
              <p className="text-sm font-black text-slate-800 dark:text-slate-100 mt-0.5">$117,500.00</p>
            </div>
            <div>
              <span className="text-2xs font-bold text-slate-400 uppercase tracking-wide">Credits Total</span>
              <p className="text-sm font-black text-slate-800 dark:text-slate-100 mt-0.5">$117,500.00</p>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Button variant="secondary" size="sm" onClick={() => setCurrentStep(2)}>Back</Button>
            <Button variant="primary" size="sm" onClick={handleNextStep} isLoading={isLoading}>
              Confirm & Post Ingestion
            </Button>
          </div>
        </div>
      )}

      {/* STEP 4: COMPLETE */}
      {currentStep === 4 && (
        <div className="p-8 rounded-2xl bg-white dark:bg-slate-900/60 border border-slate-200/50 dark:border-slate-850 shadow-sm flex flex-col items-center justify-center text-center space-y-4">
          <div className="p-4 bg-emerald-500/10 rounded-2xl text-emerald-600">
            <CheckCircle2 className="h-12 w-12" />
          </div>
          <div className="space-y-1">
            <h3 className="text-xl font-bold text-slate-800 dark:text-slate-100">Ingestion Complete</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm">
              All validated rows have been compiled into posted entry batch <span className="font-mono font-bold text-indigo-500 text-sm">JV-IMP-9874</span>.
            </p>
          </div>
          <div className="flex space-x-3 pt-4">
            <Button variant="outline" size="sm" onClick={handleReset}>Upload another file</Button>
            <Button variant="primary" size="sm" rightIcon={<ArrowRight className="h-4 w-4" />}>
              Go to History
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
