import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Building2, Users, Shield, Crown, UserPlus, CheckCircle2, AlertCircle } from 'lucide-react';
import { useAuth } from '../auth/useAuth';
import { apiClient } from '../../lib/api';
import type { OrganisationMember, InviteMemberRequest } from '../../types';

export function SettingsPage() {
  const { organisation, isCommander } = useAuth();
  const queryClient = useQueryClient();

  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<'ADMIN' | 'DISPATCHER' | 'DRIVER' | 'VIEWER'>('DISPATCHER');
  const [inviteSuccess, setInviteSuccess] = useState('');
  const [inviteError, setInviteError] = useState('');

  const { data: members, isLoading: isMembersLoading } = useQuery({
    queryKey: ['organisation-members'],
    queryFn: () => apiClient<OrganisationMember[]>('/api/v1/organisations/members'),
    enabled: !!organisation?.id,
  });

  const inviteMutation = useMutation({
    mutationFn: (data: InviteMemberRequest) =>
      apiClient<OrganisationMember>('/api/v1/organisations/members/invite', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['organisation-members'] });
      setInviteSuccess(`Invitation sent successfully to ${inviteEmail}`);
      setInviteEmail('');
      setInviteError('');
    },
    onError: (err: Error) => {
      setInviteError(err.message || 'Failed to send invitation');
      setInviteSuccess('');
    },
  });

  const handleInvite = (e: React.FormEvent) => {
    e.preventDefault();
    setInviteSuccess('');
    setInviteError('');
    inviteMutation.mutate({ email: inviteEmail, role_code: inviteRole });
  };

  return (
    <div className="space-y-8 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Workspace & RBAC Settings</h1>
        <p className="text-sm text-slate-400">
          Manage your organisation profile, member access roles, and Commander authority.
        </p>
      </div>

      {/* Organisation Details */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 space-y-6">
        <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
          <div className="rounded-xl bg-indigo-600/20 p-2.5 text-indigo-400 border border-indigo-500/30">
            <Building2 className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">{organisation?.name || 'Organisation Profile'}</h2>
            <p className="text-xs text-slate-400">Tenant identifier and formal registration parameters</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
          <div>
            <label className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Entity Legal Name</label>
            <p className="mt-1 text-base font-semibold text-slate-200">{organisation?.name || '---'}</p>
          </div>

          <div>
            <label className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Organisation Structure</label>
            <p className="mt-1 text-base font-semibold text-slate-200">{organisation?.organisation_type || '---'}</p>
          </div>

          <div>
            <label className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Workspace Status</label>
            <p className="mt-1">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                {organisation?.status || 'ACTIVE'}
              </span>
            </p>
          </div>

          <div>
            <label className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Tenant UUID</label>
            <p className="mt-1 font-mono text-xs text-slate-400 bg-slate-950 p-2 rounded-lg border border-slate-800/80 select-all">
              {organisation?.id || '---'}
            </p>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-800">
          <label className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Authentication Methods</label>
          <div className="mt-3">
            <button
              type="button"
              onClick={async () => {
                const { supabase } = await import('../../lib/supabase');
                await supabase.auth.linkIdentity({ provider: 'google', options: { redirectTo: `${window.location.origin}/auth/callback` }});
              }}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/80 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700"
            >
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              Enable / Link Google Login
            </button>
            <p className="mt-2 text-xs text-slate-500">
              Link your Google account to easily sign in without a password. For Gmail addresses, this is mandatory.
            </p>
          </div>
        </div>
      </div>

      {/* Team Members & RBAC */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-purple-600/20 p-2.5 text-purple-400 border border-purple-500/30">
              <Users className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Team Members & Access Control</h2>
              <p className="text-xs text-slate-400">Strict Commander-controlled role based permissions</p>
            </div>
          </div>
        </div>

        {/* Invite Form */}
        <form onSubmit={handleInvite} className="rounded-xl bg-slate-950/60 p-4 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
            <div className="flex items-center gap-2">
              <UserPlus className="h-4 w-4 text-indigo-400" />
              Invite Organisation Member
            </div>
            {isCommander && (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-semibold text-amber-300 border border-amber-500/20">
                <Crown className="h-3 w-3" />
                Commander Authorised
              </span>
            )}
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="email"
              placeholder="member@company.com"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              required
              className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
            />

            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value as any)}
              className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
            >
              <option value="ADMIN">Admin</option>
              <option value="DISPATCHER">Dispatcher</option>
              <option value="DRIVER">Driver</option>
              <option value="VIEWER">Viewer</option>
            </select>

            <button
              type="submit"
              disabled={inviteMutation.isPending}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 transition shadow"
            >
              <UserPlus className="h-4 w-4" />
              {inviteMutation.isPending ? 'Inviting...' : 'Send Invite'}
            </button>
          </div>

          {inviteSuccess && (
            <p className="flex items-center gap-1 text-xs text-emerald-400">
              <CheckCircle2 className="h-3.5 w-3.5" />
              {inviteSuccess}
            </p>
          )}
          {inviteError && (
            <p className="flex items-center gap-1 text-xs text-red-400">
              <AlertCircle className="h-3.5 w-3.5" />
              {inviteError}
            </p>
          )}
        </form>

        {/* Member Table */}
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="border-b border-slate-800 bg-slate-950/80 text-xs font-semibold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="px-4 py-3">Member ID</th>
                <th className="px-4 py-3">Role</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Joined / Invited</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-900/30">
              {isMembersLoading ? (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-xs text-slate-500">
                    Loading members...
                  </td>
                </tr>
              ) : members && members.length > 0 ? (
                members.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-800/30">
                    <td className="px-4 py-3 font-mono text-xs text-slate-400">{m.user_id}</td>
                    <td className="px-4 py-3">
                      {m.role_code === 'COMMANDER' ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-semibold text-amber-300 border border-amber-500/20">
                          <Crown className="h-3 w-3" />
                          Commander
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/20">
                          <Shield className="h-3 w-3" />
                          {m.role_name || m.role_code}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                          m.status === 'ACTIVE'
                            ? 'bg-emerald-500/10 text-emerald-400'
                            : 'bg-amber-500/10 text-amber-400'
                        }`}
                      >
                        {m.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {new Date(m.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-xs text-slate-500">
                    No members found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
