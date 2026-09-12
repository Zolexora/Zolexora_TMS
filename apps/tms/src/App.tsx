import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ShieldCheck, Truck, ArrowRight } from 'lucide-react';
import { LoginForm } from './components/login-form';
import { OnboardingForm } from './components/onboarding-form';
import { ProtectedRoute } from './routes/ProtectedRoute';
import { DashboardLayout } from './layouts/DashboardLayout';
import { DashboardPage } from './features/dashboard/DashboardPage';
import { BookingsPage } from './features/bookings/BookingsPage';
import { DutiesPage } from './features/duties/DutiesPage';
import { DispatchPage } from './features/dispatch/DispatchPage';
import { VehiclesPage } from './features/fleet/VehiclesPage';
import { DriversPage } from './features/fleet/DriversPage';
import { CustomersPage } from './features/fleet/CustomersPage';
import { VendorsPage } from './features/fleet/VendorsPage';
import { RateCardsPage } from './features/rate-cards/RateCardsPage';
import { BillingPage } from './features/billing/BillingPage';
import { InvoicesPage } from './features/invoices/InvoicesPage';
import { PaymentsPage } from './features/billing/PaymentsPage';
import { PayablesPage } from './features/billing/PayablesPage';
import { ExpensesPage } from './features/expenses/ExpensesPage';
import { PnLReportsPage } from './features/reports/PnLReportsPage';
import { SettingsPage } from './features/onboarding/SettingsPage';
import { AuthCallback } from './features/auth/AuthCallback';
import CompliancePage from './pages/compliance/CompliancePage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
});

function HomePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-6 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-600/20 text-indigo-400 mb-6 border border-indigo-500/30 shadow-xl">
        <Truck className="h-8 w-8" />
      </div>
      <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
        Zolexora TMS
      </h1>
      <p className="mt-4 max-w-xl text-lg text-slate-400">
        Production-grade Transport Management System managing complete operational and financial workflows.
      </p>
      
      <div className="mt-8 flex gap-4">
        <Link 
          to="/login" 
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-6 py-3 font-semibold text-white transition hover:bg-indigo-500 shadow-lg shadow-indigo-600/20"
        >
          Sign In
          <ArrowRight className="h-4 w-4" />
        </Link>
        <Link 
          to="/onboarding" 
          className="inline-flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900 px-6 py-3 font-semibold text-slate-200 transition hover:bg-slate-800"
        >
          Register Organisation
        </Link>
      </div>

      <div className="mt-12 flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-4 py-1 text-xs font-medium text-emerald-400">
        <ShieldCheck className="h-3.5 w-3.5" />
        Render Canonical API: https://api.tms.zolexora.onrender.com
      </div>
    </div>
  );
}

function AuthPageWrapper({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 p-4">
      {children}
    </div>
  );
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public Landing & Authentication */}
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<AuthPageWrapper><LoginForm /></AuthPageWrapper>} />
          <Route path="/onboarding" element={<AuthPageWrapper><OnboardingForm /></AuthPageWrapper>} />
          <Route path="/auth/callback" element={<AuthCallback />} />

          {/* Protected Workspace Navigation */}
          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/bookings" element={<BookingsPage />} />
              <Route path="/duties" element={<DutiesPage />} />
              <Route path="/dispatch" element={<DispatchPage />} />
              <Route path="/compliance/vehicles" element={<VehiclesPage />} />
              <Route path="/compliance/drivers" element={<DriversPage />} />
              <Route path="/compliance/customers" element={<CustomersPage />} />
              <Route path="/compliance/vendors" element={<VendorsPage />} />
              <Route path="/rate-cards" element={<RateCardsPage />} />
              <Route path="/billing" element={<BillingPage />} />
              <Route path="/invoices" element={<InvoicesPage />} />
              <Route path="/payments" element={<PaymentsPage />} />
              <Route path="/payables" element={<PayablesPage />} />
              <Route path="/expenses" element={<ExpensesPage />} />
              <Route path="/reports/pnl" element={<PnLReportsPage />} />
              <Route path="/compliance" element={<CompliancePage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

