import React, { useState } from 'react';
import { 
  FileBarChart, Printer, Download, RefreshCw 
} from 'lucide-react';
import { useCompany } from '../../companies/context/CompanyContext';
import { Button } from '../../../components/Button';
import { Select } from '../../../components/Select';

interface ReportLine {
  code?: string;
  name: string;
  isGroup: boolean;
  level: number;
  currentAmount: number;
  prevAmount: number;
}

export const ReportsPage: React.FC = () => {
  const { activeCompany } = useCompany();
  const [showZeroAccounts, setShowZeroAccounts] = useState(false);
  const [selectedYear, setSelectedYear] = useState('2026');
  const [selectedMonth, setSelectedMonth] = useState('07');

  const years = [
    { value: '2025', label: '2025 Fiscal Year' },
    { value: '2026', label: '2026 Fiscal Year' },
    { value: '2027', label: '2027 Fiscal Year' }
  ];

  const months = [
    { value: '01', label: 'January' },
    { value: '02', label: 'February' },
    { value: '03', label: 'March' },
    { value: '04', label: 'April' },
    { value: '05', label: 'May' },
    { value: '06', label: 'June' },
    { value: '07', label: 'July' },
    { value: '08', label: 'August' },
    { value: '09', label: 'September' },
    { value: '10', label: 'October' },
    { value: '11', label: 'November' },
    { value: '12', label: 'December' }
  ];

  // Mock report hierarchy lines
  const reportData: ReportLine[] = [
    { name: 'Revenue', isGroup: true, level: 0, currentAmount: 220000, prevAmount: 200000 },
    { code: 'REV-101', name: 'Operating Transport Revenue', isGroup: false, level: 1, currentAmount: 185000, prevAmount: 170000 },
    { code: 'REV-102', name: 'Other Service Income', isGroup: false, level: 1, currentAmount: 35000, prevAmount: 30000 },
    { name: 'Total Revenue', isGroup: true, level: 0, currentAmount: 220000, prevAmount: 200000 },
    
    { name: 'Direct Expenses', isGroup: true, level: 0, currentAmount: -102500, prevAmount: -95000 },
    { code: 'EXP-201', name: 'Fuel & Oil Cost', isGroup: false, level: 1, currentAmount: -42500, prevAmount: -40000 },
    { code: 'EXP-202', name: 'Driver & Crew Salaries', isGroup: false, level: 1, currentAmount: -60000, prevAmount: -55000 },
    { name: 'Total Direct Expenses', isGroup: true, level: 0, currentAmount: -102500, prevAmount: -95000 },
    
    { name: 'Gross Profit', isGroup: true, level: 0, currentAmount: 117500, prevAmount: 105000 },
    
    { name: 'Operating Expenses', isGroup: true, level: 0, currentAmount: -28500, prevAmount: -27000 },
    { code: 'EXP-203', name: 'Vehicle Insurance Premium', isGroup: false, level: 1, currentAmount: -18000, prevAmount: -17000 },
    { code: 'EXP-301', name: 'Rent & Office Supplies', isGroup: false, level: 1, currentAmount: -10500, prevAmount: -10000 },
    { name: 'Total Operating Expenses', isGroup: true, level: 0, currentAmount: -28500, prevAmount: -27000 },

    { name: 'Net Profit', isGroup: true, level: 0, currentAmount: 89000, prevAmount: 78000 }
  ];

  const formatCurrency = (val: number) => {
    const isNegative = val < 0;
    const absVal = Math.abs(val);
    const formatted = `$${absVal.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    return isNegative ? `(${formatted})` : formatted;
  };

  const calculateVariance = (curr: number, prev: number) => {
    return curr - prev;
  };

  const calculateVariancePercentage = (curr: number, prev: number) => {
    if (prev === 0) return 0;
    return ((curr - prev) / Math.abs(prev)) * 100;
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6 print:p-0 print:bg-white">
      {/* Header Panel */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0 print:hidden">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-slate-100 flex items-center space-x-2">
            <FileBarChart className="h-7 w-7 text-indigo-500" />
            <span>P&L Financial Reports</span>
          </h2>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Generate Income Statements for <span className="font-semibold text-indigo-500">{activeCompany?.name || 'All Companies'}</span>.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Button variant="outline" leftIcon={<Printer className="h-4 w-4" />} onClick={handlePrint}>
            Print Statement
          </Button>
          <Button variant="primary" leftIcon={<Download className="h-4 w-4" />}>
            Export to Excel
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900/60 border border-slate-200/50 dark:border-slate-850 shadow-sm grid grid-cols-1 sm:grid-cols-4 gap-4 items-end print:hidden">
        <Select 
          label="Reporting Year"
          options={years}
          value={selectedYear}
          onChange={(e) => setSelectedYear(e.target.value)}
        />
        <Select 
          label="Reporting Month"
          options={months}
          value={selectedMonth}
          onChange={(e) => setSelectedMonth(e.target.value)}
        />
        <div className="flex items-center h-full pb-3 pl-2">
          <label className="flex items-center space-x-2 text-sm font-semibold text-slate-600 dark:text-slate-400 cursor-pointer">
            <input 
              type="checkbox" 
              checked={showZeroAccounts} 
              onChange={(e) => setShowZeroAccounts(e.target.checked)}
              className="h-4 w-4 rounded border-slate-300 dark:border-slate-800 text-indigo-600 focus:ring-indigo-500"
            />
            <span>Include zero accounts</span>
          </label>
        </div>
        <div className="flex justify-end">
          <Button variant="secondary" className="w-full sm:w-auto" leftIcon={<RefreshCw className="h-4 w-4" />}>
            Recalculate
          </Button>
        </div>
      </div>

      {/* Report Sheet */}
      <div className="p-8 rounded-2xl bg-white dark:bg-slate-900/40 border border-slate-200/60 dark:border-slate-850 shadow-sm print:border-none print:shadow-none">
        
        {/* Print Header */}
        <div className="text-center pb-8 border-b border-slate-100 dark:border-slate-800 space-y-1">
          <h3 className="text-2xl font-black uppercase tracking-wider text-slate-800 dark:text-slate-100">
            PROFIT AND LOSS STATEMENT
          </h3>
          <p className="text-base font-bold text-indigo-500">{activeCompany?.name || 'ZolexoraERP Lite Group'}</p>
          <p className="text-xs text-slate-400 font-mono">
            For the period ending {months.find(m => m.value === selectedMonth)?.label} {selectedYear}
          </p>
        </div>

        {/* Report Table */}
        <div className="mt-8 overflow-x-auto">
          <table className="min-w-full text-left border-collapse">
            <thead>
              <tr className="text-xs font-mono font-semibold text-slate-400 dark:text-slate-500 uppercase border-b border-slate-200 dark:border-slate-800 pb-3">
                <th className="py-3 px-4">Account/Group</th>
                <th className="py-3 px-4 w-40 text-right">Current Month ($)</th>
                <th className="py-3 px-4 w-40 text-right">Previous Month ($)</th>
                <th className="py-3 px-4 w-32 text-right">Variance ($)</th>
                <th className="py-3 px-4 w-28 text-right">Var %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100/50 dark:divide-slate-850">
              {reportData.map((row, idx) => {
                const varAmount = calculateVariance(row.currentAmount, row.prevAmount);
                const varPct = calculateVariancePercentage(row.currentAmount, row.prevAmount);

                const isTotal = row.name.startsWith('Total ') || row.name === 'Gross Profit' || row.name === 'Net Profit';
                const isHeading = row.isGroup && !isTotal;
                
                let textClass = 'text-slate-700 dark:text-slate-300';
                let weightClass = 'font-normal';
                let paddingLeft = 'pl-4';

                if (isHeading) {
                  textClass = 'text-indigo-600 dark:text-indigo-400 uppercase tracking-wide';
                  weightClass = 'font-extrabold text-xs';
                  paddingLeft = 'pl-2';
                } else if (isTotal) {
                  textClass = 'text-slate-800 dark:text-slate-150';
                  weightClass = 'font-bold';
                  paddingLeft = 'pl-4';
                }

                if (row.level === 1) {
                  paddingLeft = 'pl-8';
                }

                return (
                  <tr 
                    key={idx} 
                    className={`hover:bg-slate-50/20 dark:hover:bg-slate-900/5 transition ${
                      isTotal ? 'bg-slate-50/30 dark:bg-slate-900/10 font-bold border-t border-slate-200 dark:border-slate-800' : ''
                    } ${row.name === 'Net Profit' || row.name === 'Gross Profit' ? 'border-b-2 border-indigo-500/20' : ''}`}
                  >
                    <td className={`py-3.5 ${paddingLeft} ${textClass} ${weightClass}`}>
                      {row.code && <span className="font-mono text-2xs text-slate-400 mr-2">{row.code}</span>}
                      {row.name}
                    </td>
                    <td className={`py-3.5 px-4 text-right font-mono ${weightClass} ${row.currentAmount < 0 ? 'text-red-500' : ''}`}>
                      {formatCurrency(row.currentAmount)}
                    </td>
                    <td className={`py-3.5 px-4 text-right font-mono text-slate-400 dark:text-slate-500`}>
                      {formatCurrency(row.prevAmount)}
                    </td>
                    <td className={`py-3.5 px-4 text-right font-mono font-semibold ${varAmount < 0 ? 'text-red-500' : 'text-emerald-500'}`}>
                      {varAmount > 0 ? '+' : ''}{formatCurrency(varAmount)}
                    </td>
                    <td className={`py-3.5 px-4 text-right font-mono font-semibold ${varPct < 0 ? 'text-red-500' : 'text-emerald-500'}`}>
                      {varPct > 0 ? '+' : ''}{varPct.toFixed(1)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
