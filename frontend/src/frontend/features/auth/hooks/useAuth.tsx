import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import type { Session } from '@supabase/supabase-js';
import { UserRole } from '../../../../shared/types';
import { roleHasPermission, type Permission } from '../../../../shared/permissions';
import { api } from '../../../api/client';
import { useRouter } from '../../../app/router';
import { supabase } from '../../../lib/supabaseClient';

interface AuthUser {
  email: string;
  role: UserRole;
  companyCodes: string[];
  allCompanyAccess: boolean;
}

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  login: (credentials: { email: string; password: string }) => Promise<void>;
  signUp: (credentials: { email: string; password: string }) => Promise<{ confirmationRequired: boolean }>;
  logout: () => Promise<void>;
  isAdmin: boolean;
  isAccountant: boolean;
  isViewer: boolean;
  can: (permission: Permission) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { navigate } = useRouter();
  // Avoids double-fetching /auth/me: the initial getSession() call and the
  // 'INITIAL_SESSION' event from onAuthStateChange can both fire on mount.
  const initialized = useRef(false);

  const loadProfile = async (session: Session | null) => {
    if (!session) {
      setUser(null);
      setToken(null);
      return;
    }
    setToken(session.access_token);
    try {
      const response = await api.get<{ user: { email: string; role: UserRole; company_codes: string[]; all_company_access: boolean } }>(
        '/auth/me',
      );
      setUser({
        email: response.user.email,
        role: response.user.role,
        companyCodes: response.user.company_codes,
        allCompanyAccess: response.user.all_company_access,
      });
    } catch (err) {
      console.error('Identity verification failed', err);
      setUser(null);
    }
  };

  useEffect(() => {
    const { data: subscription } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_OUT') {
        setUser(null);
        setToken(null);
        navigate('/login');
        return;
      }
      void loadProfile(session).finally(() => setLoading(false));
    });

    supabase.auth.getSession().then(({ data }) => {
      if (initialized.current) return;
      initialized.current = true;
      void loadProfile(data.session).finally(() => setLoading(false));
    });

    return () => subscription.subscription.unsubscribe();
  }, []);

  const login = async ({ email, password }: { email: string; password: string }) => {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
    navigate('/dashboard');
  };

  const signUp = async ({ email, password }: { email: string; password: string }) => {
    const { data, error } = await supabase.auth.signUp({ email, password });
    if (error) throw error;
    // If email confirmations are enabled in the Supabase project, there is
    // no session yet -- the person needs to click the confirmation link
    // before signing in.
    const confirmationRequired = !data.session;
    if (!confirmationRequired) navigate('/dashboard');
    return { confirmationRequired };
  };

  const logout = async () => {
    await supabase.auth.signOut();
    setUser(null);
    setToken(null);
    navigate('/login');
  };

  const isAdmin = user?.role === 'Admin';
  const isAccountant = user?.role === 'Accountant' || user?.role === 'Admin';
  const isViewer = user?.role === 'Viewer' || user?.role === 'Accountant' || user?.role === 'Admin';
  const can = (permission: Permission) => (user ? roleHasPermission(user.role, permission) : false);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, signUp, logout, isAdmin, isAccountant, isViewer, can }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
