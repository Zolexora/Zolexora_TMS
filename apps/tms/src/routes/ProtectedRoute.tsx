import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../features/auth/useAuth';
import { Loader2 } from 'lucide-react';

export function ProtectedRoute() {
  const { user, isLoading, authMe } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-400">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
          <span className="text-sm font-medium">Validating Zolexora TMS session...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // If user is authenticated but has no organisation assigned yet, redirect to onboarding
  if (authMe && !authMe.organisation_id) {
    return <Navigate to="/onboarding" replace />;
  }

  return <Outlet />;
}
