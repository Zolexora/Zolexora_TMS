import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ShieldAlert } from 'lucide-react';

const queryClient = new QueryClient();

function AdminHomePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-6 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-600/20 text-amber-400 mb-6 border border-amber-500/30">
        <ShieldAlert className="h-8 w-8" />
      </div>
      <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
        Zolexora TMS Admin Panel
      </h1>
      <p className="mt-4 max-w-xl text-lg text-slate-400">
        Platform & Developer Administration Portal. Multi-tenant quota management, audit oversight, and system diagnostics.
      </p>
    </div>
  );
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AdminHomePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
