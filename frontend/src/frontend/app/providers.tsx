import React from 'react';
import { CompanyProvider } from '../features/companies/context/CompanyContext';
import { AuthProvider } from '../features/auth/hooks/useAuth';
import { RouterProvider } from './router';
import { ThemeProvider } from './ThemeProvider';
import { PeriodProvider } from '../features/periods/context/PeriodContext';

export const AppProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider>
    <RouterProvider>
      <AuthProvider>
        <CompanyProvider><PeriodProvider>{children}</PeriodProvider></CompanyProvider>
      </AuthProvider>
    </RouterProvider>
  </ThemeProvider>
);
