import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ClipboardList,
  Search,
  AlertCircle,
  X,
  UserCheck,
  Truck,
  Send,
  CheckCircle2,
  ShieldAlert,
} from 'lucide-react';
import { apiClient } from '../../lib/api';
import type {
  Duty,
  DutyAssignRequest,
  Driver,
  Vehicle,
} from '../../types';

export function DutiesPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [selectedDuty, setSelectedDuty] = useState<Duty | null>(null);
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [formError, setFormError] = useState('');

  const [assignmentForm, setAssignmentForm] = useState<DutyAssignRequest>({
    driver_id: '',
    vehicle_id: '',
  });

  // Fetch Duties
  const { data: duties, isLoading: isDutiesLoading } = useQuery({
    queryKey: ['duties', statusFilter],
    queryFn: () => {
      const q = statusFilter !== 'ALL' ? `?status=${statusFilter}` : '';
      return apiClient<Duty[]>(`/api/v1/duties${q}`);
    },
  });

  // Fetch Drivers
  const { data: drivers } = useQuery({
    queryKey: ['drivers'],
    queryFn: () => apiClient<Driver[]>('/api/v1/drivers'),
  });

  // Fetch Vehicles
  const { data: vehicles } = useQuery({
    queryKey: ['vehicles'],
    queryFn: () => apiClient<Vehicle[]>('/api/v1/vehicles'),
  });

  // Assign Driver & Vehicle Mutation
  const assignMutation = useMutation({
    mutationFn: ({ dutyId, data }: { dutyId: string; data: DutyAssignRequest }) =>
      apiClient<Duty>(`/api/v1/duties/${dutyId}/assign`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['duties'] });
      setIsAssignModalOpen(false);
      setSelectedDuty(null);
      setFormError('');
    },
    onError: (err: Error) => setFormError(err.message),
  });

  // Dispatch Duty Mutation
  const dispatchMutation = useMutation({
    mutationFn: (dutyId: string) =>
      apiClient<Duty>(`/api/v1/duties/${dutyId}/dispatch`, {
        method: 'POST',
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['duties'] }),
    onError: (err: Error) => alert(`Failed to dispatch duty: ${err.message}`),
  });

  // Driver Accept Mutation
  const acceptMutation = useMutation({
    mutationFn: (dutyId: string) =>
      apiClient<Duty>(`/api/v1/duties/${dutyId}/accept`, {
        method: 'POST',
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['duties'] }),
    onError: (err: Error) => alert(`Error accepting duty: ${err.message}`),
  });

  const openAssignModal = (d: Duty) => {
    setSelectedDuty(d);
    setAssignmentForm({
      driver_id: d.driver_id || '',
      vehicle_id: d.vehicle_id || '',
    });
    setFormError('');
    setIsAssignModalOpen(true);
  };

  const getDriverName = (driverId?: string) => {
    if (!driverId) return 'Unassigned';
    const d = drivers?.find((drv) => drv.id === driverId);
    return d ? `${d.full_name} (${d.phone})` : driverId.slice(0, 8);
  };

  const getVehicleReg = (vehicleId?: string) => {
    if (!vehicleId) return 'Unassigned';
    const v = vehicles?.find((veh) => veh.id === vehicleId);
    return v ? `${v.registration_number} (${v.vehicle_type})` : vehicleId.slice(0, 8);
  };

  const filteredDuties = duties?.filter((duty) =>
    duty.duty_number.toLowerCase().includes(search.toLowerCase()) ||
    duty.booking_id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Duty Management & Allocation</h1>
          <p className="text-sm text-slate-400">
            Authoritative duty rosters, conflict-preventing vehicle allocation, and driver dispatch.
          </p>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex flex-wrap gap-2">
          {['ALL', 'ALLOCATED', 'DISPATCHED', 'ARRIVED_PICKUP', 'IN_TRANSIT', 'DUTY_COMPLETED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                statusFilter === st
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-900/60 border border-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2 max-w-xs w-full">
          <Search className="h-4 w-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search duties..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none w-full"
          />
        </div>
      </div>

      {/* Duties Table */}
      <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/40">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="border-b border-slate-800 bg-slate-950/80 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <tr>
              <th className="px-5 py-3.5">Duty Number</th>
              <th className="px-5 py-3.5">Allocated Driver</th>
              <th className="px-5 py-3.5">Allocated Vehicle</th>
              <th className="px-5 py-3.5">Scheduled Window</th>
              <th className="px-5 py-3.5">Status</th>
              <th className="px-5 py-3.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {isDutiesLoading ? (
              <tr>
                <td colSpan={6} className="px-5 py-8 text-center text-slate-500">
                  Loading transport duties...
                </td>
              </tr>
            ) : filteredDuties?.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-5 py-12 text-center text-slate-500">
                  <ClipboardList className="mx-auto h-8 w-8 text-slate-600 mb-2" />
                  No duty rosters matching filter.
                </td>
              </tr>
            ) : (
              filteredDuties?.map((duty) => (
                <tr key={duty.id} className="hover:bg-slate-800/30 transition">
                  <td className="px-5 py-4 font-mono font-medium text-white">
                    {duty.duty_number}
                    {duty.notes && (
                      <p className="text-xs text-slate-400 font-sans mt-0.5 max-w-xs truncate">{duty.notes}</p>
                    )}
                  </td>
                  <td className="px-5 py-4 text-slate-200">
                    <div className="flex items-center gap-2">
                      <UserCheck className={`h-4 w-4 ${duty.driver_id ? 'text-emerald-400' : 'text-slate-600'}`} />
                      <span>{getDriverName(duty.driver_id)}</span>
                    </div>
                  </td>
                  <td className="px-5 py-4 text-slate-200">
                    <div className="flex items-center gap-2">
                      <Truck className={`h-4 w-4 ${duty.vehicle_id ? 'text-indigo-400' : 'text-slate-600'}`} />
                      <span>{getVehicleReg(duty.vehicle_id)}</span>
                    </div>
                  </td>
                  <td className="px-5 py-4 text-xs text-slate-300">
                    <div>{new Date(duty.scheduled_start_time).toLocaleString()}</div>
                    <div className="text-slate-500">to {new Date(duty.scheduled_end_time).toLocaleTimeString()}</div>
                  </td>
                  <td className="px-5 py-4">
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                        duty.status === 'ALLOCATED'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : duty.status === 'DISPATCHED'
                          ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                          : duty.status === 'ARRIVED_PICKUP'
                          ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                          : duty.status === 'IN_TRANSIT'
                          ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                          : duty.status === 'DUTY_COMPLETED'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}
                    >
                      {duty.status}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-right space-x-2">
                    {duty.status === 'ALLOCATED' && (
                      <>
                        <button
                          onClick={() => openAssignModal(duty)}
                          className="inline-flex items-center gap-1 rounded-lg bg-slate-800 border border-slate-700 px-2.5 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition"
                        >
                          {duty.driver_id && duty.vehicle_id ? 'Reallocate' : 'Allocate'}
                        </button>
                        {duty.driver_id && duty.vehicle_id && (
                          <button
                            onClick={() => dispatchMutation.mutate(duty.id)}
                            disabled={dispatchMutation.isPending}
                            className="inline-flex items-center gap-1 rounded-lg bg-indigo-600/20 border border-indigo-500/30 px-3 py-1.5 text-xs font-semibold text-indigo-300 hover:bg-indigo-600 hover:text-white transition"
                          >
                            <Send className="h-3.5 w-3.5" />
                            Dispatch
                          </button>
                        )}
                      </>
                    )}
                    {duty.status === 'DISPATCHED' && (
                      <button
                        onClick={() => acceptMutation.mutate(duty.id)}
                        disabled={acceptMutation.isPending}
                        className="inline-flex items-center gap-1 rounded-lg bg-emerald-600/20 border border-emerald-500/30 px-2.5 py-1.5 text-xs font-semibold text-emerald-400 hover:bg-emerald-600 hover:text-white transition"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Driver Accept
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Allocation Modal */}
      {isAssignModalOpen && selectedDuty && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
              <div>
                <h3 className="text-lg font-bold text-white">Allocate Driver & Vehicle</h3>
                <p className="text-xs text-slate-400">
                  Duty <span className="font-mono text-indigo-400 font-semibold">{selectedDuty.duty_number}</span>
                </p>
              </div>
              <button
                onClick={() => setIsAssignModalOpen(false)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {formError && (
              <div className="mb-4 flex items-center gap-2 rounded-xl bg-rose-500/10 border border-rose-500/20 p-3 text-sm text-rose-400">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form
              onSubmit={(e) => {
                e.preventDefault();
                assignMutation.mutate({
                  dutyId: selectedDuty.id,
                  data: assignmentForm,
                });
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Select Driver *</label>
                <select
                  required
                  value={assignmentForm.driver_id}
                  onChange={(e) => setAssignmentForm({ ...assignmentForm, driver_id: e.target.value })}
                  className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                >
                  <option value="">Select an enrolled driver...</option>
                  {drivers?.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.full_name} — {d.license_number} ({d.status})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Select Vehicle *</label>
                <select
                  required
                  value={assignmentForm.vehicle_id}
                  onChange={(e) => setAssignmentForm({ ...assignmentForm, vehicle_id: e.target.value })}
                  className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                >
                  <option value="">Select a fleet vehicle...</option>
                  {vehicles?.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.registration_number} — {v.vehicle_type} ({v.status})
                    </option>
                  ))}
                </select>
              </div>

              <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-3 text-xs text-slate-400">
                <div className="flex items-center gap-1.5 font-semibold text-slate-300 mb-1">
                  <ShieldAlert className="h-3.5 w-3.5 text-amber-400" />
                  Compliance & Conflict Prevention
                </div>
                The system strictly checks driver commercial license validity and rejects overlapping
                duty assignments for both drivers and fleet vehicles.
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAssignModalOpen(false)}
                  className="rounded-xl border border-slate-800 px-4 py-2 text-sm font-medium text-slate-400 hover:bg-slate-800 hover:text-white transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={assignMutation.isPending}
                  className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 transition disabled:opacity-50"
                >
                  {assignMutation.isPending ? 'Verifying & Allocating...' : 'Confirm Allocation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

