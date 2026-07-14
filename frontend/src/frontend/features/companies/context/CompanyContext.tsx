import React, { createContext, useContext, useState, useEffect } from 'react';
import { Company } from '../../../../shared/types';
import { api } from '../../../api/client';
import { useAuth } from '../../auth/hooks/useAuth';

interface CompanyContextType {
  companies: Company[];
  activeCompany: Company | null;
  setActiveCompany: (company: Company | null) => void;
  loading: boolean;
  refreshCompanies: () => Promise<void>;
}

const CompanyContext = createContext<CompanyContextType | undefined>(undefined);

export const CompanyProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [activeCompany, setActiveCompanyState] = useState<Company | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchCompanies = async () => {
    if (!user) {
      setCompanies([]);
      setActiveCompanyState(null);
      return;
    }
    setLoading(true);
    try {
      const data = (await api.get<Company[]>('/companies')) as Company[];
      setCompanies(data);
      
      const savedCode = localStorage.getItem('active_company_code');
      const found = data.find((c: Company) => c.code === savedCode);
      if (found) {
        setActiveCompanyState(found);
      } else if (data.length > 0) {
        setActiveCompanyState(data[0]);
        localStorage.setItem('active_company_code', data[0].code);
      } else {
        setActiveCompanyState(null);
      }
    } catch (err) {
      console.error("Failed to fetch companies", err);
      // Reset state on failure
      setCompanies([]);
      setActiveCompanyState(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompanies();
  }, [user]);

  const setActiveCompany = (company: Company | null) => {
    setActiveCompanyState(company);
    if (company) {
      localStorage.setItem('active_company_code', company.code);
    } else {
      localStorage.removeItem('active_company_code');
    }
  };

  return (
    <CompanyContext.Provider value={{ 
      companies, 
      activeCompany, 
      setActiveCompany, 
      loading, 
      refreshCompanies: fetchCompanies 
    }}>
      {children}
    </CompanyContext.Provider>
  );
};

export const useCompany = () => {
  const context = useContext(CompanyContext);
  if (!context) {
    throw new Error('useCompany must be used within a CompanyProvider');
  }
  return context;
};
