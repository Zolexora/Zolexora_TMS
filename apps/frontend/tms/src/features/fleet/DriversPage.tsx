import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Users, Plus, Search, AlertCircle, X, ShieldCheck } from 'lucide-react';
import { apiClient } from '../../lib/api';
import type { Driver, DriverCreate } from '../../types';
import { EntityComplianceManager } from '../compliance/EntityComplianceManager';

export function DriversPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [complianceModalId, setComplianceModalId] = useState<string | null>(null);
  const [formError, setFormError] = useState('');

  const [formData, setFormData] = useState<DriverCreate>({
    full_name: '',
    phone: '',
    alternate_phone: '',
    email: '',
    license_number: '',
    license_type: 'HMV',
    badge_number: '',
    aadhaar_last4: '',
    pan: '',
    driver_type: 'PERMANENT',
  });

  const { data: drivers, isLoading } = useQuery({
    queryKey: ['drivers', search],
    queryFn: () => {
      const q = search ? `?search=${encodeURIComponent(search)}` : '';
      return apiClient<Driver[]>(`/api/v1/drivers${q}`);
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: DriverCreate) =>
      apiClient<Driver>('/api/v1/drivers', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drivers'] });
      setIsModalOpen(false);
      setFormData({
        full_name: '',
        phone: '',
        alternate_phone: '',
        email: '',
        license_number: '',
        license_type: 'HMV',
        badge_number: '',
        aadhaar_last4: '',
        pan: '',
        driver_type: 'PERMANENT',
      });
      setFormError('');
    },
    onError: (err: any) => {
      setFormError(err.message || 'Failed to enroll driver');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.full_name.trim() || !formData.phone.trim() || !formData.license_number.trim()) {
      setFormError('Name, Phone, and License Number are required.');
      return;
    }
    
    // Auto clean license plate
    const cleanedLicense = formData.license_number.toUpperCase().replace(/\s+/g, '');
    
    createMutation.mutate({
      ...formData,
      license_number: cleanedLicense,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Drivers Roster</h1>
          <p className="text-sm text-slate-400">Driver roster, commercial license verification, and mobile app allocation.</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition"
        >
          <Plus className="h-4 w-4" />
          Enroll Driver
        </button>
      </div>

      <div className="flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2 max-w-md">
        <Search className="h-4 w-4 text-slate-500" />
        <input
          type="text"
          placeholder="Search driver by name, phone, or license..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none w-full"
        />
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-800/80 text-xs uppercase text-slate-400">
            <tr>
              <th className="px-5 py-4 font-semibold">Driver Name & Phone</th>
              <th className="px-5 py-4 font-semibold">License & KYC</th>
              <th className="px-5 py-4 font-semibold">Type</th>
              <th className="px-5 py-4 font-semibold">Status</th>
              <th className="px-5 py-4 font-semibold">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="px-5 py-8 text-center text-xs text-slate-500">
                  Loading drivers...
                </td>
              </tr>
            ) : drivers && drivers.length > 0 ? (
              drivers.map((d) => (
                <tr key={d.id} className="hover:bg-slate-800/30 transition">
                  <td className="px-5 py-4">
                    <div className="font-semibold text-white">{d.full_name}</div>
                    <div className="text-xs text-slate-400 font-mono">{d.phone}</div>
                  </td>
                  <td className="px-5 py-4 text-xs font-mono">
                    <div className="text-indigo-400">{d.license_number} ({d.license_type})</div>
                    <div className="text-slate-500 text-[11px]">{d.aadhaar_last4 ? `Aadhaar: ••••${d.aadhaar_last4}` : ''}</div>
                  </td>
                  <td className="px-5 py-4 text-xs">
                    <span className="rounded-md bg-slate-800 px-2 py-0.5 text-xs text-slate-300">
                      {d.driver_type}
                    </span>
                  </td>
                  <td className="px-5 py-4">
                    <span
                      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                        d.status === 'AVAILABLE'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : d.status === 'ON_DUTY'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : 'bg-slate-700/20 text-slate-400'
                      }`}
                    >
                      {d.status}
                    </span>
                  </td>
                  <td className="px-5 py-4">
                    <button
                      onClick={() => setComplianceModalId(d.id)}
                      className="inline-flex items-center gap-1 rounded bg-slate-800 px-2 py-1 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-white"
                      title="Manage Compliance"
                    >
                      <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
                      Docs
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="px-5 py-12 text-center">
                  <div className="flex flex-col items-center justify-center text-center">
                    <Users className="h-8 w-8 text-slate-600 mb-2" />
                    <p className="text-sm font-semibold text-slate-300">No drivers registered</p>
                    <p className="text-xs text-slate-500 mt-0.5">Click 'Enroll Driver' to add transport drivers with commercial licenses.</p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Compliance Modal */}
      {complianceModalId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="w-full max-w-2xl rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4 my-8">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-emerald-400" />
                Driver Compliance
              </h2>
              <button onClick={() => setComplianceModalId(null)} className="text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="dark">
              <EntityComplianceManager entityType="DRIVER" entityId={complianceModalId} />
            </div>
          </div>
        </div>
      )}

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4 my-8">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-lg font-bold text-white">Enroll New Driver</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-medium text-slate-300">Full Name *</label>
                <input
                  type="text"
                  required
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  placeholder="e.g. Ramesh Kumar Yadav"
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300">Primary Phone *</label>
                  <input
                    type="text"
                    required
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    placeholder="+919988776655"
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300">Alternate Phone</label>
                  <input
                    type="text"
                    value={formData.alternate_phone}
                    onChange={(e) => setFormData({ ...formData, alternate_phone: e.target.value })}
                    placeholder="+919876543210"
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300">Driving License Number *</label>
                  <input
                    type="text"
                    required
                    value={formData.license_number}
                    onChange={(e) => setFormData({ ...formData, license_number: e.target.value.toUpperCase() })}
                    placeholder="DL1420110012345"
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white font-mono text-xs focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300">License Type</label>
                  <select
                    value={formData.license_type}
                    onChange={(e) => setFormData({ ...formData, license_type: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="HMV">Heavy Motor Vehicle (HMV)</option>
                    <option value="TRANS">Transport Vehicle (TRANS)</option>
                    <option value="LMV">Light Motor Vehicle (LMV)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300">Aadhaar (Last 4 Digits)</label>
                  <input
                    type="text"
                    maxLength={4}
                    value={formData.aadhaar_last4}
                    onChange={(e) => setFormData({ ...formData, aadhaar_last4: e.target.value })}
                    placeholder="5678"
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white font-mono text-xs focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300">Driver Employment Type</label>
                  <select
                    value={formData.driver_type}
                    onChange={(e) => setFormData({ ...formData, driver_type: e.target.value as any })}
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="PERMANENT">Permanent Roster</option>
                    <option value="CONTRACT">Contract Staff</option>
                    <option value="MARKET">Market / Vendor Driver</option>
                  </select>
                </div>
              </div>

              {formError && (
                <p className="flex items-center gap-1 text-xs text-red-400">
                  <AlertCircle className="h-3.5 w-3.5" />
                  {formError}
                </p>
              )}

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
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
                  className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 transition"
                >
                  {createMutation.isPending ? 'Enrolling...' : 'Enroll Driver'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
