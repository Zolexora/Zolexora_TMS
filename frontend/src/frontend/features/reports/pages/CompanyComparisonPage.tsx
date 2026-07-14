import React, { useState } from 'react';
import { 
  Building2, AlertTriangle, Download, Layers 
} from 'lucide-react';
import { Button } from '../../../components/Button';

interface CompareRow {
  code?: string;
  name: string;
  isGroup: boolean;
  values: Record<string, number>; // companyCode -> amount
}

export const CompanyComparisonPage: React.FC = () => {
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>(['ARAVALI', 'HIMALAYA']);
  const [selectedYear, setSelectedYear] = useState('2026');
  const [selectedMonth, setSelectedMonth] = useState('07');

  // Mock comparison data
  const compareData: CompareRow[] = [
    { name: 'Revenue', isGroup: true, values: { ARAVALI: 220000, HIMALAYA: 145000, SIVALIK: 98000 } },
    { code: 'REV-101', name: 'Operating Transport Revenue', isGroup: false, values: { ARAVALI: 185000, HIMALAYA: 120000, SIVALIK: 80000 } },
    { code: 'REV-102', name: 'Other Service Income', isGroup: false, values: { ARAVALI: 35000, HIMALAYA: 25000, SIVALIK: 18000 } },
    { name: 'Total Revenue', isGroup: true, values: { ARAVALI: 220000, HIMALAYA: 145000, SIVALIK: 98000 } },

    { name: 'Direct Expenses', isGroup: true, values: { ARAVALI: -102500, HIMALAYA: -78000, SIVALIK: -45000 } },
    { code: 'EXP-201', name: 'Fuel & Oil Cost', isGroup: false, values: { ARAVALI: -42500, HIMALAYA: -33000, SIVALIK: -15000 } },
    { code: 'EXP-202', name: 'Driver & Crew Salaries', isGroup: false, values: { ARAVALI: -60000, HIMALAYA: -45000, SIVALIK: -30000 } },
    { name: 'Total Direct Expenses', isGroup: true, values: { ARAVALI: -102500, HIMALAYA: -78000, SIVALIK: -45000 } },

    { name: 'Gross Profit', isGroup: true, values: { ARAVALI: 117500, HIMALAYA: 67000, SIVALIK: 53000 } },

    { name: 'Operating Expenses', isGroup: true, values: { ARAVALI: -28500, HIMALAYA: -19500, SIVALIK: -12000 } },
    { code: 'EXP-203', name: 'Vehicle Insurance Premium', isGroup: false, values: { ARAVALI: -18000, HIMALAYA: -12000, SIVALIK: -7000 } },
    { code: 'EXP-301', name: 'Rent & Office Supplies', isGroup: false, values: { ARAVALI: -10500, HIMALAYA: -7500, SIVALIK: -5000 } },
    { name: 'Total Operating Expenses', isGroup: true, values: { ARAVALI: -28500, HIMALAYA: -19500, SIVALIK: -12000 } },

    { name: 'Net Profit', isGroup: true, values: { ARAVALI: 89000, HIMALAYA: 47500, SIVALIK: 41000 } }
  ];

  // Helper check if selected companies have different currencies
  const getCurrency = (code: string) => {
    if (code === 'ARAVALI') return 'USD';
    if (code === 'HIMALAYA') return 'EUR';
    return 'INR';
  };

  const selectedCurrencies = selectedCompanies.map(c => getCurrency(c));
  const uniqueCurrencies = Array.from(new Set(selectedCurrencies));
  const hasCurrencyMismatch = uniqueCurrencies.length > 1;

  const handleToggleCompany = (code: string) => {
    if (selectedCompanies.includes(code)) {
      if (selectedCompanies.length === 1) return; // Keep at least one
      setSelectedCompanies(selectedCompanies.filter(c => c !== code));
    } else {
      setSelectedCompanies([...selectedCompanies, code]);
    }
  };

  const formatCurrency = (val: number, compCode: string) => {
    const currency = getCurrency(compCode);
    const symbol = currency === 'USD' ? '$' : currency === 'EUR' ? '€' : '₹';
    const isNegative = val < 0;
    const absVal = Math.abs(val);
    const formatted = `${symbol}${absVal.toLocaleString('en-US', { minimumFractionDigits: 0 })}`;
    return isNegative ? `(${formatted})` : formatted;
  };

  return (
    <div className="space-y-6">
      {/* Header Panel */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-slate-100 flex items-center space-x-2">
            <Layers className="h-7 w-7 text-indigo-500" />
            <span>Company Comparison</span>
          </h2>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Compare monthly profit and loss metrics side-by-side across companies.
          </p>
        </div>
        <Button variant="primary" leftIcon={<Download className="h-4 w-4" />}>
          Export Matrix
        </Button>
      </div>

      {/* Selector Panel */}
      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900/60 border border-slate-200/50 dark:border-slate-850 shadow-sm grid grid-cols-1 md:grid-cols-3 gap-5">
        
        {/* Years & Months */}
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-slate-700 dark:text-slate-350">Reporting Context</label>
          <div className="flex space-x-2">
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(e.target.value)}
              className="w-full bg-slate-50 dark:bg-slate-850 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none cursor-pointer"
            >
              <option value="2026">2026 Fiscal</option>
              <option value="2025">2025 Fiscal</option>
            </select>
            <select
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
              className="w-full bg-slate-50 dark:bg-slate-850 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none cursor-pointer"
            >
              <option value="07">July</option>
              <option value="06">June</option>
            </select>
          </div>
        </div>

        {/* Selected Companies checkbox list */}
        <div className="md:col-span-2 space-y-2">
          <label className="block text-sm font-semibold text-slate-700 dark:text-slate-350">Selected Scope</label>
          <div className="flex items-center space-x-4 pt-1.5">
            {['ARAVALI', 'HIMALAYA', 'SIVALIK'].map(code => {
              const isChecked = selectedCompanies.includes(code);
              return (
                <button
                  key={code}
                  onClick={() => handleToggleCompany(code)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold border transition ${
                    isChecked 
                      ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-600 dark:text-indigo-400 font-bold' 
                      : 'bg-transparent border-slate-200 dark:border-slate-800 text-slate-400'
                  }`}
                >
                  <Building2 className="h-4 w-4" />
                  <span>{code} ({getCurrency(code)})</span>
                </button>
              );
            })}
          </div>
        </div>

      </div>

      {/* Currency mismatch Warning alert */}
      {hasCurrencyMismatch && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 text-xs flex items-start space-x-3">
          <AlertTriangle className="h-5 w-5 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h5 className="font-bold">Consolidated Totals Blocked</h5>
            <p className="leading-relaxed">
              Consolidated totals cannot be displayed because selected companies use different currencies: <span className="font-mono font-bold uppercase">{uniqueCurrencies.join(', ')}</span>. Cross-currency summation without exchange rates is mathematically invalid.
            </p>
          </div>
        </div>
      )}

      {/* Comparison Matrix Table */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900/40 border border-slate-200/60 dark:border-slate-850 shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full text-left border-collapse">
            <thead>
              <tr className="text-xs font-mono font-semibold text-slate-400 dark:text-slate-500 uppercase border-b border-slate-200 dark:border-slate-800 pb-3">
                <th className="py-3 px-4">Account/Group</th>
                {selectedCompanies.map(c => (
                  <th key={c} className="py-3 px-4 w-48 text-right">
                    {c} ({getCurrency(c)})
                  </th>
                ))}
                {!hasCurrencyMismatch && (
                  <th className="py-3 px-4 w-48 text-right bg-slate-50 dark:bg-slate-900/40 font-bold">
                    Consolidated
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-850 text-sm">
              {compareData.map((row, idx) => {
                const isTotal = row.name.startsWith('Total ') || row.name === 'Gross Profit' || row.name === 'Net Profit';
                const isHeading = row.isGroup && !isTotal;
                
                let textClass = 'text-slate-700 dark:text-slate-350';
                let weightClass = 'font-normal';
                let paddingLeft = 'pl-4';

                if (isHeading) {
                  textClass = 'text-indigo-600 dark:text-indigo-400 uppercase tracking-wide';
                  weightClass = 'font-extrabold text-xs';
                  paddingLeft = 'pl-2';
                } else if (isTotal) {
                  textClass = 'text-slate-800 dark:text-slate-150';
                  weightClass = 'font-bold';
                }

                if (row.code) {
                  paddingLeft = 'pl-8';
                }

                // Calculate consolidation sum
                const consolidatedSum = selectedCompanies.reduce((sum, c) => sum + (row.values[c] || 0), 0);

                return (
                  <tr 
                    key={idx} 
                    className={`hover:bg-slate-50/20 dark:hover:bg-slate-900/5 transition ${
                      isTotal ? 'bg-slate-50/30 dark:bg-slate-900/10 font-bold border-t border-slate-200 dark:border-slate-800' : ''
                    }`}
                  >
                    <td className={`py-3 px-4 ${paddingLeft} ${textClass} ${weightClass}`}>
                      {row.code && <span className="font-mono text-2xs text-slate-400 mr-2">{row.code}</span>}
                      {row.name}
                    </td>
                    
                    {selectedCompanies.map(c => {
                      const amount = row.values[c] || 0;
                      return (
                        <td key={c} className={`py-3 px-4 text-right font-mono ${weightClass} ${amount < 0 ? 'text-red-500' : ''}`}>
                          {formatCurrency(amount, c)}
                        </td>
                      );
                    })}

                    {!hasCurrencyMismatch && (
                      <td className={`py-3 px-4 text-right font-mono bg-slate-50/50 dark:bg-slate-900/20 ${weightClass} ${consolidatedSum < 0 ? 'text-red-500' : ''}`}>
                        {formatCurrency(consolidatedSum, selectedCompanies[0])}
                      </td>
                    )}
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
