import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Users, Shield, ShieldAlert, Key } from 'lucide-react';
import { apiClient } from '../../lib/api';
import type { MemberWithRoleResponse, RoleResponse } from '../../types';

export function MembersPage() {
  const queryClient = useQueryClient();
  const [selectedMember, setSelectedMember] = useState<MemberWithRoleResponse | null>(null);

  const { data: members, isLoading: membersLoading } = useQuery({
    queryKey: ['org-members'],
    queryFn: () => apiClient<MemberWithRoleResponse[]>('/api/v1/organisations/members-with-roles'),
  });

  const { data: roles, isLoading: rolesLoading } = useQuery({
    queryKey: ['org-roles'],
    queryFn: () => apiClient<RoleResponse[]>('/api/v1/organisations/roles'),
  });

  const assignRoleMutation = useMutation({
    mutationFn: ({ memberId, roleId }: { memberId: string; roleId: string | null }) => 
      apiClient(`/api/v1/organisations/members/${memberId}/role`, {
        method: 'PUT',
        body: JSON.stringify({ role_id: roleId }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['org-members'] });
      setSelectedMember(null);
    },
  });

  if (membersLoading || rolesLoading) {
    return <div className="p-8 text-slate-400">Loading members...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-white flex items-center gap-2">
            <Users className="h-6 w-6 text-indigo-400" />
            Organisation Members
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            Manage your team, assign roles, and apply permission overrides.
          </p>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50">
        <table className="min-w-full divide-y divide-slate-800">
          <thead className="bg-slate-900">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">Member</th>
              <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">Role</th>
              <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">Status</th>
              <th className="px-6 py-4 text-right text-xs font-medium uppercase tracking-wider text-slate-400">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 bg-transparent">
            {members?.map((member) => (
              <tr key={member.member_id} className="hover:bg-slate-800/50 transition">
                <td className="whitespace-nowrap px-6 py-4">
                  <div className="font-medium text-slate-200">{member.member_id}</div>
                  {member.is_commander && (
                    <div className="mt-1 flex items-center gap-1 text-xs font-medium text-amber-500">
                      <ShieldAlert className="h-3.5 w-3.5" />
                      Commander
                    </div>
                  )}
                </td>
                <td className="whitespace-nowrap px-6 py-4">
                  {member.is_commander ? (
                    <span className="text-sm text-slate-500 italic">Full Access</span>
                  ) : member.role_id ? (
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-medium text-indigo-300 border border-indigo-500/20">
                      <Shield className="h-3.5 w-3.5" />
                      {member.role_name}
                    </span>
                  ) : (
                    <span className="text-sm text-slate-500">No Role</span>
                  )}
                </td>
                <td className="whitespace-nowrap px-6 py-4">
                  <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400 border border-emerald-500/20">
                    {member.status}
                  </span>
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                  {!member.is_commander && (
                    <button
                      onClick={() => setSelectedMember(member)}
                      className="text-indigo-400 hover:text-indigo-300 transition"
                    >
                      Manage Access
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedMember && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Key className="h-5 w-5 text-indigo-400" />
              Manage Access
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Assign Role
                </label>
                <select
                  value={selectedMember.role_id || ''}
                  onChange={(e) => {
                    assignRoleMutation.mutate({
                      memberId: selectedMember.member_id,
                      roleId: e.target.value || null,
                    });
                  }}
                  disabled={assignRoleMutation.isPending}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm text-white focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="">-- No Role --</option>
                  {roles?.filter(r => r.status === 'ACTIVE').map(role => (
                    <option key={role.id} value={role.id}>
                      {role.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="rounded-lg bg-slate-800/50 p-4 border border-slate-700/50">
                <p className="text-sm text-slate-400">
                  Permission overrides (GRANT/RESTRICT) can be managed here in future updates, enabling specific capabilities to be added or removed independent of the assigned role.
                </p>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedMember(null)}
                className="rounded-lg px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800 transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
