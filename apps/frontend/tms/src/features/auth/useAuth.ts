import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import type { Session, User } from '@supabase/supabase-js';
import { supabase } from '../../lib/supabase';
import { apiClient } from '../../lib/api';
import type { AuthMeResponse, Organisation } from '../../types';

export function useAuth() {
  const queryClient = useQueryClient();
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isSessionLoading, setIsSessionLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session: currentSession } }) => {
      setSession(currentSession);
      setUser(currentSession?.user ?? null);
      setIsSessionLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, newSession) => {
      setSession(newSession);
      setUser(newSession?.user ?? null);
      setIsSessionLoading(false);
      queryClient.invalidateQueries({ queryKey: ['auth-me'] });
      queryClient.invalidateQueries({ queryKey: ['organisation-me'] });
    });

    return () => subscription.unsubscribe();
  }, [queryClient]);

  const {
    data: authMe,
    isLoading: isAuthMeLoading,
    error: authMeError,
  } = useQuery({
    queryKey: ['auth-me', session?.access_token],
    queryFn: () => apiClient<AuthMeResponse>('/api/v1/auth/me'),
    enabled: !!session?.access_token,
  });

  const {
    data: organisation,
    isLoading: isOrgLoading,
    error: orgError,
  } = useQuery({
    queryKey: ['organisation-me', session?.access_token],
    queryFn: () => apiClient<Organisation>('/api/v1/organisations/me'),
    enabled: !!session?.access_token && !!authMe?.organisation_id,
  });

  const signOut = async () => {
    await supabase.auth.signOut();
    queryClient.clear();
  };

  const isCommander = authMe?.role_code === 'COMMANDER';

  return {
    session,
    user,
    authMe,
    organisation,
    isLoading: isSessionLoading || (!!session && (isAuthMeLoading || isOrgLoading)),
    error: authMeError || orgError,
    isCommander,
    signOut,
  };
}
