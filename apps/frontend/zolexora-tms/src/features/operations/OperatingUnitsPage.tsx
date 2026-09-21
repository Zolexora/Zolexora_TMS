import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Building, Plus, Search, AlertCircle, X, MapPin } from 'lucide-react';
import { apiClient } from '../../lib/api';

export function OperatingUnitsPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formError, setFormError] = useState('');
  
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    status: 'ACTIVE'
  });

  const { data: units, isLoading } = useQuery({
    queryKey: ['operating-units'],
    queryFn: () => apiClient<any[]>('/api/v1/operations/operating-units'),
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) =>
      apiClient<any>('/api/v1/operations/operating-units', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['operating-units'] });
      setIsModalOpen(false);
      setFormData({ code: '', name: '', status: 'ACTIVE' });
      setFormError('');
    },
    onError: (err: any) => {
      setFormError(err.message || 'Failed to create operating unit');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.code.trim()) {
      setFormError('Code and Name are required');
      return;
    }
    createMutation.mutate(formData);
  };

  const filtered = units?.filter(u => 
    u.name.toLowerCase().includes(search.toLowerCase()) || 
    u.code.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Building className="h-6 w-6 text-indigo-400" />
            Operating Units
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Manage your organization's business units, branches, or divisions.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-500"
        >
          <Plus className="h-4 w-4" />
          Add Unit
        </button>
      </div>

      <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/50 p-2">
        <Search className="h-5 w-5 text-slate-400 ml-2" />
        <input
          type="text"
          placeholder="Search by name or code..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 bg-transparent px-2 py-1 text-white focus:outline-none"
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {isLoading ? (
          <div className="col-span-full py-12 text-center text-slate-400">Loading units...</div>
        ) : filtered?.length === 0 ? (
          <div className="col-span-full py-12 text-center text-slate-400 border border-dashed border-slate-800 rounded-xl">
            No operating units found. Add one to get started.
          </div>
        ) : (
          filtered?.map((unit) => (
            <div key={unit.id} className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 transition hover:border-slate-700">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-white">{unit.name}</h3>
                    <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs font-medium text-slate-300">
                      {unit.code}
                    </span>
                  </div>
                  <div className="mt-3 flex items-center gap-1.5 text-sm text-slate-400">
                    <MapPin className="h-4 w-4" />
                    <span>0 Locations mapped</span>
                  </div>
                </div>
                <div className={`rounded-full px-2 py-1 text-xs font-medium ${unit.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
                  {unit.status}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-white">Add Operating Unit</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300">Unit Code</label>
                <input
                  type="text"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                  placeholder="e.g. MUM-01"
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300">Unit Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Mumbai HQ"
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                />
              </div>

              {formError && (
                <p className="flex items-center gap-1 text-xs text-red-400">
                  <AlertCircle className="h-3.5 w-3.5" />
                  {formError}
                </p>
              )}

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-lg px-4 py-2 text-sm text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50"
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Unit'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
