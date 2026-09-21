import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Shield, Plus, Edit2, Archive } from 'lucide-react';
import { apiClient } from '../../lib/api';
import type { RoleResponse } from '../../types';
import { RoleBuilder } from './RoleBuilder';

export function RolesPage() {
  const queryClient = useQueryClient();
  const [isBuilderOpen, setIsBuilderOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<RoleResponse | null>(null);

  const { data: roles, isLoading } = useQuery({
    queryKey: ['org-roles'],
    queryFn: () => apiClient<RoleResponse[]>('/api/v1/organisations/roles'),
  });

  const archiveRoleMutation = useMutation({
    mutationFn: (roleId: string) => apiClient(`/api/v1/organisations/roles/${roleId}/archive`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['org-roles'] });
    },
  });

  if (isLoading) {
    return <div className="p-8 text-slate-400">Loading roles...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-white flex items-center gap-2">
            <Shield className="h-6 w-6 text-indigo-400" />
            Roles & Permissions
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            Define roles and configure granular access control capabilities.
          </p>
        </div>
        <button
          onClick={() => {
            setEditingRole(null);
            setIsBuilderOpen(true);
          }}
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-500"
        >
          <Plus className="h-4 w-4" />
          Create Role
        </button>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50">
        <table className="min-w-full divide-y divide-slate-800">
          <thead className="bg-slate-900">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">Role Name</th>
              <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">Capabilities</th>
              <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">Members</th>
              <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-400">Status</th>
              <th className="px-6 py-4 text-right text-xs font-medium uppercase tracking-wider text-slate-400">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 bg-transparent">
            {roles?.map((role) => (
              <tr key={role.id} className="hover:bg-slate-800/50 transition">
                <td className="whitespace-nowrap px-6 py-4">
                  <div className="font-medium text-slate-200">{role.name}</div>
                  {role.description && <div className="text-sm text-slate-500">{role.description}</div>}
                  {role.source === 'SYSTEM' && (
                    <span className="mt-1 inline-flex items-center rounded-full bg-slate-800 px-2 py-0.5 text-xs font-medium text-slate-300">
                      System Managed
                    </span>
                  )}
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-slate-400">
                    {role.current_permissions?.length || 0} permissions granted
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-slate-400">
                    {role.member_count} members
                  </div>
                </td>
                <td className="whitespace-nowrap px-6 py-4">
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      role.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-800 text-slate-400 border border-slate-700'
                    }`}
                  >
                    {role.status}
                  </span>
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                  <div className="flex items-center justify-end gap-3">
                    <button
                      onClick={() => {
                        setEditingRole(role);
                        setIsBuilderOpen(true);
                      }}
                      className="text-slate-400 hover:text-indigo-400 transition"
                      title="Edit Role"
                    >
                      <Edit2 className="h-4 w-4" />
                    </button>
                    {role.source !== 'SYSTEM' && role.status === 'ACTIVE' && (
                      <button
                        onClick={() => archiveRoleMutation.mutate(role.id)}
                        className="text-slate-400 hover:text-red-400 transition"
                        title="Archive Role"
                      >
                        <Archive className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {(!roles || roles.length === 0) && (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-sm text-slate-500">
                  No roles found. Create one to get started.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {isBuilderOpen && (
        <RoleBuilder
          role={editingRole}
          onClose={() => setIsBuilderOpen(false)}
          onSuccess={() => {
            setIsBuilderOpen(false);
            queryClient.invalidateQueries({ queryKey: ['org-roles'] });
          }}
        />
      )}
    </div>
  );
}
