import { createContext, useContext, ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { RuntimeConfiguration } from '../types/runtime';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../features/auth/useAuth';

const ApplicationRuntimeContext = createContext<RuntimeConfiguration | null>(null);

export function ApplicationRuntimeProvider({ children }: { children: ReactNode }) {
  const { session } = useAuth();
  
  const { data: runtimeConfig, isLoading, error } = useQuery<RuntimeConfiguration>({
    queryKey: ['application-runtime', session?.user?.id],
    queryFn: () => apiClient<RuntimeConfiguration>('/api/v1/application/runtime'),
    enabled: !!session, // Only fetch when authenticated
    staleTime: 1000 * 60 * 5, // Cache for 5 mins
  });

  if (!session) {
    return <>{children}</>;
  }

  if (isLoading) {
    return (
      <div className="flex h-screen w-full flex-col items-center justify-center bg-slate-950 text-slate-400">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-500 mb-4" />
        <p className="text-sm font-medium">Loading Application Configuration...</p>
      </div>
    );
  }

  if (error || !runtimeConfig) {
    return (
      <div className="flex h-screen w-full flex-col items-center justify-center bg-slate-950 text-slate-400">
        <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-center">
          <h2 className="text-lg font-semibold text-red-400 mb-2">Application Error</h2>
          <p className="text-sm text-red-300">Failed to load application runtime configuration.</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 rounded bg-slate-800 px-4 py-2 text-sm text-white hover:bg-slate-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <ApplicationRuntimeContext.Provider value={runtimeConfig}>
      {children}
    </ApplicationRuntimeContext.Provider>
  );
}

export function useApplicationRuntime() {
  const context = useContext(ApplicationRuntimeContext);
  if (context === null) {
    throw new Error('useApplicationRuntime must be used within an ApplicationRuntimeProvider');
  }
  return context as RuntimeConfiguration;
}
