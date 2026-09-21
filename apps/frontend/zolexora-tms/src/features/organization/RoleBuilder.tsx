import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { X, Check } from 'lucide-react';
import { apiClient } from '../../lib/api';
import type { RoleResponse, CapabilityRegistryResponse, RoleCreateRequest, RoleUpdateRequest, RolePermission } from '../../types';

interface RoleBuilderProps {
  role: RoleResponse | null;
  onClose: () => void;
  onSuccess: () => void;
}

export function RoleBuilder({ role, onClose, onSuccess }: RoleBuilderProps) {
  const queryClient = useQueryClient();
  const isEditing = !!role;

  const [name, setName] = useState(role?.name || '');
  const [description, setDescription] = useState(role?.description || '');
  const [selectedPermissions, setSelectedPermissions] = useState<Set<string>>(
    new Set(role?.current_permissions.map(p => `${p.module_code}.${p.page_code}.${p.action_code}`) || [])
  );
  const [changeNote, setChangeNote] = useState('');

  const { data: registry, isLoading: registryLoading } = useQuery({
    queryKey: ['capability-registry'],
    queryFn: () => apiClient<CapabilityRegistryResponse>('/api/v1/capabilities'),
  });

  const saveMutation = useMutation({
    mutationFn: (data: RoleCreateRequest | RoleUpdateRequest) => {
      if (isEditing) {
        return apiClient(`/api/v1/organisations/roles/${role.id}`, {
          method: 'PATCH',
          body: JSON.stringify(data),
        });
      }
      return apiClient('/api/v1/organisations/roles', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['org-roles'] });
      onSuccess();
    },
  });

  const handleTogglePermission = (capStr: string) => {
    const next = new Set(selectedPermissions);
    if (next.has(capStr)) {
      next.delete(capStr);
    } else {
      next.add(capStr);
    }
    setSelectedPermissions(next);
  };

  const handleToggleModule = (mod: any) => {
    const next = new Set(selectedPermissions);
    const modCaps = mod.pages.flatMap((p: any) => p.actions.map((a: any) => `${mod.code}.${p.code}.${a.code}`));
    const allSelected = modCaps.every((c: string) => next.has(c));
    
    modCaps.forEach((c: string) => {
      if (allSelected) {
        next.delete(c);
      } else {
        next.add(c);
      }
    });
    setSelectedPermissions(next);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const perms: RolePermission[] = Array.from(selectedPermissions).map(capStr => {
      const [module_code, page_code, action_code] = capStr.split('.');
      return { module_code, page_code, action_code };
    });

    saveMutation.mutate({
      name,
      description,
      permissions: perms,
      change_note: changeNote || (isEditing ? 'Updated role' : 'Created role'),
    });
  };

  if (registryLoading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm">
        <div className="text-slate-400">Loading capability registry...</div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 sm:p-6">
      <div className="flex h-full w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 p-6">
          <h3 className="text-xl font-semibold text-white">
            {isEditing ? 'Edit Role' : 'Create Role'}
          </h3>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-1 flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-6 space-y-8">
            {role?.source === 'SYSTEM' && (
              <div className="rounded-lg bg-indigo-500/10 p-4 border border-indigo-500/20 text-sm text-indigo-200">
                This is a system-managed role. You cannot change its name, but you may alter its permissions for your organization.
              </div>
            )}
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300">Role Name</label>
                <input
                  type="text"
                  required
                  disabled={role?.source === 'SYSTEM'}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-white placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
                  placeholder="e.g. Dispatch Manager"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-300">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-white placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  placeholder="Describe the purpose of this role"
                  rows={2}
                />
              </div>

              {isEditing && (
                <div>
                  <label className="block text-sm font-medium text-slate-300">Change Note (Required for auditing)</label>
                  <input
                    type="text"
                    required
                    value={changeNote}
                    onChange={(e) => setChangeNote(e.target.value)}
                    className="mt-1 block w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-white placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    placeholder="e.g. Added vendor management permissions"
                  />
                </div>
              )}
            </div>

            <div>
              <h4 className="text-lg font-medium text-white mb-4">Capabilities</h4>
              <div className="space-y-6">
                {registry?.modules.map(mod => (
                  <div key={mod.code} className="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden">
                    <div 
                      className="flex items-center justify-between bg-slate-800/50 px-4 py-3 cursor-pointer hover:bg-slate-800 transition"
                      onClick={() => handleToggleModule(mod)}
                    >
                      <h5 className="font-medium text-white">{mod.name}</h5>
                    </div>
                    <div className="p-4 space-y-4">
                      {mod.pages.map(page => (
                        <div key={page.code}>
                          <h6 className="text-sm font-medium text-slate-400 mb-2">{page.name}</h6>
                          <div className="flex flex-wrap gap-2">
                            {page.actions.map(action => {
                              const capStr = `${mod.code}.${page.code}.${action.code}`;
                              const isSelected = selectedPermissions.has(capStr);
                              return (
                                <button
                                  key={action.code}
                                  type="button"
                                  onClick={() => handleTogglePermission(capStr)}
                                  className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition ${
                                    isSelected 
                                      ? 'bg-indigo-600 text-white shadow-sm' 
                                      : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-300'
                                  }`}
                                >
                                  {isSelected && <Check className="h-3 w-3" />}
                                  {action.name}
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 border-t border-slate-800 p-6 bg-slate-900">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saveMutation.isPending}
              className="rounded-lg bg-indigo-600 px-6 py-2 text-sm font-medium text-white hover:bg-indigo-500 transition disabled:opacity-50"
            >
              {saveMutation.isPending ? 'Saving...' : 'Save Role'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
