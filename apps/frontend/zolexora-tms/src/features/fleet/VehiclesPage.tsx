import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Truck, Plus, Search, AlertCircle, X, Navigation, ShieldCheck } from 'lucide-react';
import { apiClient } from '../../lib/api';
import type { Vehicle, VehicleCreate } from '../../types';
import { EntityComplianceManager } from '../compliance/EntityComplianceManager';

export function VehiclesPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [complianceModalId, setComplianceModalId] = useState<string | null>(null);
  const [formError, setFormError] = useState('');

  const [formData, setFormData] = useState<VehicleCreate>({
    registration_number: '',
    vehicle_type: 'TRUCK',
    ownership_type: 'OWNED',
    make: '',
    model: '',
    fuel_type: 'DIESEL',
    payload_capacity_kg: '',
    odometer_km: '0.00',
    fastag_id: '',
    gps_device_id: '',
  });

  const { data: vehicles, isLoading } = useQuery({
    queryKey: ['vehicles', search],
    queryFn: () => {
      const q = search ? `?search=${encodeURIComponent(search)}` : '';
      return apiClient<Vehicle[]>(`/api/v1/vehicles${q}`);
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: VehicleCreate) =>
      apiClient<Vehicle>('/api/v1/vehicles', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vehicles'] });
      setIsModalOpen(false);
      setFormData({
        registration_number: '',
        vehicle_type: 'TRUCK',
        ownership_type: 'OWNED',
        make: '',
        model: '',
        fuel_type: 'DIESEL',
        payload_capacity_kg: '',
        odometer_km: '0.00',
        fastag_id: '',
        gps_device_id: '',
      });
      setFormError('');
    },
    onError: (err: any) => {
      setFormError(err.message || 'Failed to create vehicle');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.registration_number.trim()) {
      setFormError('Registration number is required.');
      return;
    }
    
    // Auto format number plate
    const cleanedPlate = formData.registration_number.toUpperCase().replace(/\s+/g, '');
    
    createMutation.mutate({
      ...formData,
      registration_number: cleanedPlate,
      payload_capacity_kg: formData.payload_capacity_kg ? formData.payload_capacity_kg.toString() : undefined,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Fleet Vehicles</h1>
          <p className="text-sm text-slate-400">Manage heavy commercial vehicles, ownership, and tracking devices.</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition"
        >
          <Plus className="h-4 w-4" />
          Add Vehicle
        </button>
      </div>

      <div className="flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2 max-w-md">
        <Search className="h-4 w-4 text-slate-500" />
        <input
          type="text"
          placeholder="Search by registration number..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none w-full"
        />
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-800/80 text-xs uppercase text-slate-400">
            <tr>
              <th className="px-5 py-4 font-semibold">Registration</th>
              <th className="px-5 py-4 font-semibold">Type & Ownership</th>
              <th className="px-5 py-4 font-semibold">Specs</th>
              <th className="px-5 py-4 font-semibold">Telematics</th>
              <th className="px-5 py-4 font-semibold">Odometer</th>
              <th className="px-5 py-4 font-semibold">Status</th>
              <th className="px-5 py-4 font-semibold">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {isLoading ? (
              <tr>
                <td colSpan={7} className="px-5 py-8 text-center text-xs text-slate-500">
                  Loading vehicles...
                </td>
              </tr>
            ) : vehicles && vehicles.length > 0 ? (
              vehicles.map((v) => (
                <tr key={v.id} className="hover:bg-slate-800/30 transition">
                  <td className="px-5 py-4">
                    <div className="font-mono font-bold text-white text-base">{v.registration_number}</div>
                    <div className="text-xs text-slate-400">{v.make || ''} {v.model || ''}</div>
                  </td>
                  <td className="px-5 py-4 text-xs">
                    <div className="font-medium text-slate-200">{v.vehicle_type}</div>
                    <div className="text-indigo-400 text-[11px] font-semibold">{v.ownership_type}</div>
                  </td>
                  <td className="px-5 py-4 text-xs">
                    <div>{v.payload_capacity_kg ? `${v.payload_capacity_kg} kg` : 'Standard'}</div>
                    <div className="text-slate-500">{v.fuel_type}</div>
                  </td>
                  <td className="px-5 py-4 text-xs font-mono">
                    <div className="flex items-center gap-1 text-slate-300">
                      <Navigation className="h-3 w-3 text-cyan-400" />
                      {v.gps_device_id || 'No GPS'}
                    </div>
                    <div className="text-[11px] text-slate-500">{v.fastag_id ? `FASTag: ${v.fastag_id.slice(-6)}` : ''}</div>
                  </td>
                  <td className="px-5 py-4 font-mono text-xs text-slate-300">
                    {Number(v.odometer_km).toLocaleString('en-IN')} KM
                  </td>
                  <td className="px-5 py-4">
                    <span
                      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                        v.status === 'AVAILABLE'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : v.status === 'ON_DUTY'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : 'bg-red-500/10 text-red-400 border border-red-500/20'
                      }`}
                    >
                      {v.status}
                    </span>
                  </td>
                  <td className="px-5 py-4">
                    <button
                      onClick={() => setComplianceModalId(v.id)}
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
                <td colSpan={7} className="px-5 py-12 text-center">
                  <div className="flex flex-col items-center justify-center text-center">
                    <Truck className="h-8 w-8 text-slate-600 mb-2" />
                    <p className="text-sm font-semibold text-slate-300">No vehicles registered</p>
                    <p className="text-xs text-slate-500 mt-0.5">Click 'Add Vehicle' to register commercial transport trucks.</p>
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
                Vehicle Compliance
              </h2>
              <button onClick={() => setComplianceModalId(null)} className="text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="dark">
              <EntityComplianceManager entityType="VEHICLE" entityId={complianceModalId} />
            </div>
          </div>
        </div>
      )}

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4 my-8">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-lg font-bold text-white">Register Commercial Vehicle</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-medium text-slate-300">Registration Number (Number Plate) *</label>
                <input
                  type="text"
                  required
                  value={formData.registration_number}
                  onChange={(e) => setFormData({ ...formData, registration_number: e.target.value.toUpperCase().replace(/\s+/g, '') })}
                  placeholder="e.g. MH12AB1234"
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white font-mono font-bold text-sm tracking-wider focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300">Vehicle Type</label>
                  <select
                    value={formData.vehicle_type}
                    onChange={(e) => setFormData({ ...formData, vehicle_type: e.target.value as any })}
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="TRUCK">Open Truck</option>
                    <option value="CONTAINER">Container Body</option>
                    <option value="TRAILER">Semi-Trailer</option>
                    <option value="TANKER">Fuel Tanker</option>
                    <option value="TIPPER">Tipper / Dumper</option>
                    <option value="TEMPO">Tempo / LCV</option>
                    <option value="PICKUP">Pickup</option>
                    <option value="OTHER">Other Heavy Vehicle</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300">Ownership Type</label>
                  <select
                    value={formData.ownership_type}
                    onChange={(e) => setFormData({ ...formData, ownership_type: e.target.value as any })}
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="OWNED">Self Owned</option>
                    <option value="LEASED">Leased</option>
                    <option value="ATTACHED">Market / Attached</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300">Make / Manufacturer</label>
                  <input
                    type="text"
                    value={formData.make}
                    onChange={(e) => setFormData({ ...formData, make: e.target.value })}
                    placeholder="e.g. Tata Motors"
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300">Model</label>
                  <input
                    type="text"
                    value={formData.model}
                    onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                    placeholder="e.g. Signa 4825.TK"
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300">Fuel Type</label>
                  <select
                    value={formData.fuel_type}
                    onChange={(e) => setFormData({ ...formData, fuel_type: e.target.value as any })}
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="DIESEL">Diesel</option>
                    <option value="CNG">CNG</option>
                    <option value="ELECTRIC">Electric</option>
                    <option value="PETROL">Petrol</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300">Payload (KG)</label>
                  <input
                    type="number"
                    value={formData.payload_capacity_kg}
                    onChange={(e) => setFormData({ ...formData, payload_capacity_kg: e.target.value })}
                    placeholder="25000"
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300">Odometer (KM)</label>
                  <input
                    type="number"
                    value={formData.odometer_km}
                    onChange={(e) => setFormData({ ...formData, odometer_km: e.target.value })}
                    placeholder="0"
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300">FASTag ID / Barcode</label>
                  <input
                    type="text"
                    value={formData.fastag_id}
                    onChange={(e) => setFormData({ ...formData, fastag_id: e.target.value.toUpperCase() })}
                    placeholder="34161FA123456"
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white font-mono text-xs focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300">GPS Device IMEI / ID</label>
                  <input
                    type="text"
                    value={formData.gps_device_id}
                    onChange={(e) => setFormData({ ...formData, gps_device_id: e.target.value.toUpperCase() })}
                    placeholder="GPS-TRACK-9988"
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white font-mono text-xs focus:border-indigo-500 focus:outline-none"
                  />
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
                  {createMutation.isPending ? 'Registering...' : 'Register Vehicle'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
