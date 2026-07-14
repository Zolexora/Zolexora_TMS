import React from 'react';
import { useAuth } from '../features/auth/hooks/useAuth';
import { LoginPage } from '../features/auth/pages/LoginPage';
import { AppRouter } from './router';
import { LoadingState } from '../components/LoadingState';

export const App: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <LoadingState message="Retrieving active session..." />
      </div>
    );
  }

  return user ? <AppRouter user={user} /> : <LoginPage />;
};

export default App;
