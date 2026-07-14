import React, { createContext, useContext, useEffect, useState } from 'react';
import type { FinancialPeriod, FinancialYear } from '../../../../shared/types';
import { api } from '../../../api/client';
import { useCompany } from '../../companies/context/CompanyContext';

interface PeriodContextValue {
  years: FinancialYear[];
  periods: FinancialPeriod[];
  activeYear: FinancialYear | null;
  activePeriod: FinancialPeriod | null;
  loading: boolean;
  setActiveYear: (year: FinancialYear | null) => void;
  setActivePeriod: (period: FinancialPeriod | null) => void;
  refreshYears: () => Promise<void>;
  refreshPeriods: () => Promise<void>;
}

const PeriodContext = createContext<PeriodContextValue | undefined>(undefined);

export const PeriodProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { activeCompany } = useCompany();
  const [years, setYears] = useState<FinancialYear[]>([]);
  const [periods, setPeriods] = useState<FinancialPeriod[]>([]);
  const [activeYear, setActiveYearState] = useState<FinancialYear | null>(null);
  const [activePeriod, setActivePeriodState] = useState<FinancialPeriod | null>(null);
  const [loading, setLoading] = useState(false);

  const refreshYears = async () => {
    if (!activeCompany) {
      setYears([]); setActiveYearState(null); setPeriods([]); setActivePeriodState(null); return;
    }
    setLoading(true);
    try {
      const data = await api.get<FinancialYear[]>(`/financial-years?company_code=${encodeURIComponent(activeCompany.code)}`);
      setYears(data);
      const saved = localStorage.getItem(`active_financial_year:${activeCompany.code}`);
      const selected = data.find((year) => year.id === saved && year.is_active)
        ?? data.find((year) => year.is_active)
        ?? data[0]
        ?? null;
      setActiveYearState(selected);
    } catch (error) {
      console.error('Unable to load financial years', error);
      setYears([]);
      setActiveYearState(null);
    } finally {
      setLoading(false);
    }
  };

  const refreshPeriods = async () => {
    if (!activeCompany || !activeYear) {
      setPeriods([]); setActivePeriodState(null); return;
    }
    setLoading(true);
    try {
      const data = await api.get<FinancialPeriod[]>(
        `/financial-periods?company_code=${encodeURIComponent(activeCompany.code)}&financial_year_id=${encodeURIComponent(activeYear.id)}`,
      );
      setPeriods(data);
      const saved = localStorage.getItem(`active_financial_period:${activeCompany.code}`);
      const currentCode = new Date().toISOString().slice(0, 7);
      const selected = data.find((period) => period.id === saved && period.is_active)
        ?? data.find((period) => period.period_code === currentCode && period.is_active)
        ?? data.find((period) => period.is_active)
        ?? data[0]
        ?? null;
      setActivePeriodState(selected);
    } catch (error) {
      console.error('Unable to load financial periods', error);
      setPeriods([]);
      setActivePeriodState(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void refreshYears(); }, [activeCompany?.code]);
  useEffect(() => { void refreshPeriods(); }, [activeCompany?.code, activeYear?.id]);

  const setActiveYear = (year: FinancialYear | null) => {
    setActiveYearState(year);
    if (activeCompany && year) localStorage.setItem(`active_financial_year:${activeCompany.code}`, year.id);
  };

  const setActivePeriod = (period: FinancialPeriod | null) => {
    setActivePeriodState(period);
    if (activeCompany && period) localStorage.setItem(`active_financial_period:${activeCompany.code}`, period.id);
  };

  return (
    <PeriodContext.Provider value={{
      years, periods, activeYear, activePeriod, loading,
      setActiveYear, setActivePeriod, refreshYears, refreshPeriods,
    }}>
      {children}
    </PeriodContext.Provider>
  );
};

export function usePeriod() {
  const context = useContext(PeriodContext);
  if (!context) throw new Error('usePeriod must be used within PeriodProvider');
  return context;
}
