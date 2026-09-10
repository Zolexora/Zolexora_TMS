import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  RefreshCw,
  Truck,
  User,
  MapPin,
  Gauge,
  CheckCircle2,
  Navigation,
  X,
  AlertCircle,
  FileCheck2,
} from 'lucide-react';
import { apiClient } from '../../lib/api';
import type {
  DispatchBoardItem,
  DutyLifecycleStatus,
  Trip,
  TripStartRequest,
  TripCompleteRequest,
} from '../../types';

const STATUS_COLUMNS: { key: DutyLifecycleStatus; label: string; color: string }[] = [
  { key: 'ALLOCATED', label: 'Allocated', color: 'border-amber-500/30 bg-amber-500/5 text-amber-400' },
  { key: 'DISPATCHED', label: 'Dispatched', color: 'border-purple-500/30 bg-purple-500/5 text-purple-400' },
  { key: 'ARRIVED_PICKUP', label: 'At Pickup', color: 'border-cyan-500/30 bg-cyan-500/5 text-cyan-400' },
  { key: 'IN_TRANSIT', label: 'In Transit', color: 'border-indigo-500/30 bg-indigo-500/5 text-indigo-400' },
  { key: 'ARRIVED_DROP', label: 'At Destination', color: 'border-blue-500/30 bg-blue-500/5 text-blue-400' },
  { key: 'DUTY_COMPLETED', label: 'Completed', color: 'border-emerald-500/30 bg-emerald-500/5 text-emerald-400' },
];

export function DispatchPage() {
  const queryClient = useQueryClient();
  const [wsConnected, setWsConnected] = useState(false);
  const [startTripModalDuty, setStartTripModalDuty] = useState<DispatchBoardItem | null>(null);
  const [completeTripModalDuty, setCompleteTripModalDuty] = useState<DispatchBoardItem | null>(null);
  const [formError, setFormError] = useState('');

  // Trip Start State
  const [startOdo, setStartOdo] = useState('0.00');

  // Trip Complete State
  const [completeForm, setCompleteForm] = useState({
    end_odometer: '0.00',
    toll_amount: '0.00',
    fuel_amount: '0.00',
    parking_amount: '0.00',
    waiting_minutes: 0,
    notes: '',
  });

  // Query dispatch board items
  const { data: boardItems, refetch } = useQuery({
    queryKey: ['dispatch-board'],
    queryFn: () => apiClient<DispatchBoardItem[]>('/api/v1/dispatch/board'),
    refetchInterval: 15000, // Background fallback polling
  });

  // Query current trips to find trip for complete modal
  const { data: trips } = useQuery({
    queryKey: ['trips'],
    queryFn: () => apiClient<Trip[]>('/api/v1/trips'),
  });

  // Real-time WebSocket connection to /ws/ops/{org_id}
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: ReturnType<typeof setTimeout>;

    const connectWebSocket = async () => {
      try {
        const authMe = await apiClient<{ organisation_id: string }>('/api/v1/auth/me');
        if (!authMe.organisation_id) return;

        const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsHost = window.location.hostname === 'localhost' ? 'localhost:8000' : 'api.tms.zolexora.onrender.com';
        const wsUrl = `${wsProto}//${wsHost}/ws/ops/${authMe.organisation_id}`;

        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          setWsConnected(true);
        };

        ws.onmessage = () => {
          // Reactively invalidate queries when ops events arrive
          queryClient.invalidateQueries({ queryKey: ['dispatch-board'] });
          queryClient.invalidateQueries({ queryKey: ['duties'] });
          queryClient.invalidateQueries({ queryKey: ['trips'] });
        };

        ws.onclose = () => {
          setWsConnected(false);
          reconnectTimeout = setTimeout(connectWebSocket, 5000);
        };

        ws.onerror = () => {
          ws?.close();
        };
      } catch {
        // Fallback silently to REST polling
      }
    };

    connectWebSocket();

    return () => {
      clearTimeout(reconnectTimeout);
      ws?.close();
    };
  }, [queryClient]);

  // Milestone Mutations
  const arrivePickupMutation = useMutation({
    mutationFn: (dutyId: string) =>
      apiClient(`/api/v1/duties/${dutyId}/arrived-pickup`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dispatch-board'] });
      queryClient.invalidateQueries({ queryKey: ['duties'] });
    },
    onError: (err: Error) => alert(`Error: ${err.message}`),
  });

  const arriveDropMutation = useMutation({
    mutationFn: (dutyId: string) =>
      apiClient(`/api/v1/duties/${dutyId}/arrived-drop`, { method: 'POST' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dispatch-board'] });
      queryClient.invalidateQueries({ queryKey: ['duties'] });
    },
    onError: (err: Error) => alert(`Error: ${err.message}`),
  });

  // Start Trip Mutation
  const startTripMutation = useMutation({
    mutationFn: ({ dutyId, req }: { dutyId: string; req: TripStartRequest }) =>
      apiClient<Trip>(`/api/v1/trips/duties/${dutyId}/start`, {
        method: 'POST',
        body: JSON.stringify(req),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dispatch-board'] });
      queryClient.invalidateQueries({ queryKey: ['duties'] });
      queryClient.invalidateQueries({ queryKey: ['trips'] });
      setStartTripModalDuty(null);
      setFormError('');
    },
    onError: (err: Error) => setFormError(err.message),
  });

  // Complete Trip Mutation
  const completeTripMutation = useMutation({
    mutationFn: ({ tripId, req }: { tripId: string; req: TripCompleteRequest }) =>
      apiClient<Trip>(`/api/v1/trips/${tripId}/complete`, {
        method: 'POST',
        body: JSON.stringify(req),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dispatch-board'] });
      queryClient.invalidateQueries({ queryKey: ['duties'] });
      queryClient.invalidateQueries({ queryKey: ['trips'] });
      setCompleteTripModalDuty(null);
      setFormError('');
    },
    onError: (err: Error) => setFormError(err.message),
  });

  const handleStartTripSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!startTripModalDuty) return;
    startTripMutation.mutate({
      dutyId: startTripModalDuty.id,
      req: {
        start_odometer: startOdo as any,
        start_location: { address: startTripModalDuty.pickup_address },
      },
    });
  };

  const handleCompleteTripSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!completeTripModalDuty) return;

    const matchingTrip = trips?.find((t) => t.duty_id === completeTripModalDuty.id);
    if (!matchingTrip) {
      setFormError('Active trip record not found for this duty.');
      return;
    }

    if (parseFloat(completeForm.end_odometer) < parseFloat(matchingTrip.start_odometer)) {
      setFormError(
        `Ending odometer (${completeForm.end_odometer} KM) cannot be less than starting odometer (${matchingTrip.start_odometer} KM)`
      );
      return;
    }

    completeTripMutation.mutate({
      tripId: matchingTrip.id,
      req: {
        end_odometer: completeForm.end_odometer as any,
        end_location: { address: completeTripModalDuty.drop_address },
        toll_amount: completeForm.toll_amount as any,
        fuel_amount: completeForm.fuel_amount as any,
        parking_amount: completeForm.parking_amount as any,
        waiting_minutes: Number(completeForm.waiting_minutes),
        notes: completeForm.notes,
      },
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Live Dispatch Tower</h1>
          <p className="text-sm text-slate-400">
            Real-time stage orchestration, driver telemetry, and trip milestone control.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            className="rounded-xl border border-slate-800 bg-slate-900/60 p-2 text-slate-400 hover:text-white transition"
            title="Refresh Board"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
          <div
            className={`flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold ${
              wsConnected
                ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
                : 'border-amber-500/30 bg-amber-500/10 text-amber-400'
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                wsConnected ? 'bg-emerald-400 animate-ping' : 'bg-amber-400'
              }`}
            />
            {wsConnected ? 'WebSocket Live' : 'REST Polling (15s)'}
          </div>
        </div>
      </div>

      {/* Kanban Stages Board */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {STATUS_COLUMNS.map((col) => {
          const itemsInCol = boardItems?.filter((item) => item.status === col.key) || [];
          return (
            <div
              key={col.key}
              className="flex flex-col rounded-2xl border border-slate-800 bg-slate-900/30 p-3.5 min-h-[500px]"
            >
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
                <span className={`text-xs font-bold uppercase tracking-wider ${col.color.split(' ')[2]}`}>
                  {col.label}
                </span>
                <span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs font-mono font-semibold text-slate-300">
                  {itemsInCol.length}
                </span>
              </div>

              <div className="space-y-3 flex-1 overflow-y-auto">
                {itemsInCol.length === 0 ? (
                  <div className="flex h-32 items-center justify-center text-center text-xs text-slate-600">
                    Empty
                  </div>
                ) : (
                  itemsInCol.map((duty) => (
                    <div
                      key={duty.id}
                      className="rounded-xl border border-slate-800 bg-slate-900/90 p-3.5 shadow-md hover:border-slate-700 transition space-y-2.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-white">{duty.duty_number}</span>
                        <span className="text-[10px] font-mono text-slate-400">{duty.booking_number}</span>
                      </div>

                      {duty.customer_name && (
                        <div className="text-xs font-medium text-slate-300 truncate">
                          {duty.customer_name}
                        </div>
                      )}

                      <div className="space-y-1 text-xs text-slate-400">
                        <div className="flex items-center gap-1.5 text-slate-300 truncate">
                          <User className="h-3 w-3 text-indigo-400 flex-shrink-0" />
                          <span className="truncate">{duty.driver_name || 'Driver unassigned'}</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-slate-300 truncate">
                          <Truck className="h-3 w-3 text-emerald-400 flex-shrink-0" />
                          <span className="truncate">{duty.vehicle_registration || 'Vehicle unassigned'}</span>
                        </div>
                      </div>

                      <div className="rounded-lg bg-slate-950/60 p-2 text-[11px] text-slate-400 space-y-1">
                        <div className="flex items-start gap-1 text-slate-300 truncate">
                          <MapPin className="h-3 w-3 text-amber-400 flex-shrink-0 mt-0.5" />
                          <span className="truncate">{duty.pickup_address}</span>
                        </div>
                        <div className="flex items-start gap-1 text-slate-400 truncate">
                          <Navigation className="h-3 w-3 text-blue-400 flex-shrink-0 mt-0.5" />
                          <span className="truncate">{duty.drop_address}</span>
                        </div>
                      </div>

                      {/* Milestone Advance Controls */}
                      <div className="pt-2 border-t border-slate-800/80">
                        {duty.status === 'DISPATCHED' && (
                          <button
                            onClick={() => arrivePickupMutation.mutate(duty.id)}
                            disabled={arrivePickupMutation.isPending}
                            className="w-full inline-flex items-center justify-center gap-1.5 rounded-lg bg-cyan-600/20 border border-cyan-500/30 py-1.5 text-xs font-semibold text-cyan-300 hover:bg-cyan-600 hover:text-white transition"
                          >
                            <MapPin className="h-3.5 w-3.5" />
                            Arrived Pickup
                          </button>
                        )}

                        {duty.status === 'ARRIVED_PICKUP' && (
                          <button
                            onClick={() => {
                              setStartTripModalDuty(duty);
                              setStartOdo('50000.00');
                              setFormError('');
                            }}
                            className="w-full inline-flex items-center justify-center gap-1.5 rounded-lg bg-indigo-600/20 border border-indigo-500/30 py-1.5 text-xs font-semibold text-indigo-300 hover:bg-indigo-600 hover:text-white transition"
                          >
                            <Gauge className="h-3.5 w-3.5" />
                            Start Trip
                          </button>
                        )}

                        {duty.status === 'IN_TRANSIT' && (
                          <button
                            onClick={() => arriveDropMutation.mutate(duty.id)}
                            disabled={arriveDropMutation.isPending}
                            className="w-full inline-flex items-center justify-center gap-1.5 rounded-lg bg-blue-600/20 border border-blue-500/30 py-1.5 text-xs font-semibold text-blue-300 hover:bg-blue-600 hover:text-white transition"
                          >
                            <Navigation className="h-3.5 w-3.5" />
                            Arrived Destination
                          </button>
                        )}

                        {duty.status === 'ARRIVED_DROP' && (
                          <button
                            onClick={() => {
                              const matchingTrip = trips?.find((t) => t.duty_id === duty.id);
                              setCompleteTripModalDuty(duty);
                              setCompleteForm({
                                end_odometer: matchingTrip ? (parseFloat(matchingTrip.start_odometer) + 50).toFixed(2) : '50050.00',
                                toll_amount: '0.00',
                                fuel_amount: '0.00',
                                parking_amount: '0.00',
                                waiting_minutes: 0,
                                notes: '',
                              });
                              setFormError('');
                            }}
                            className="w-full inline-flex items-center justify-center gap-1.5 rounded-lg bg-emerald-600/20 border border-emerald-500/30 py-1.5 text-xs font-semibold text-emerald-300 hover:bg-emerald-600 hover:text-white transition"
                          >
                            <FileCheck2 className="h-3.5 w-3.5" />
                            Complete Trip & Duty
                          </button>
                        )}

                        {duty.status === 'DUTY_COMPLETED' && (
                          <div className="flex items-center justify-center gap-1 text-[11px] font-semibold text-emerald-400 py-1">
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            Billing Ready Record
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal: Start Trip */}
      {startTripModalDuty && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
              <div>
                <h3 className="text-lg font-bold text-white">Initiate Trip Execution</h3>
                <p className="text-xs text-slate-400">
                  Duty <span className="font-mono text-indigo-400 font-semibold">{startTripModalDuty.duty_number}</span>
                </p>
              </div>
              <button
                onClick={() => setStartTripModalDuty(null)}
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

            <form onSubmit={handleStartTripSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Starting Odometer (KM) *</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={startOdo}
                  onChange={(e) => setStartOdo(e.target.value)}
                  className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-3 text-xs text-slate-400">
                <span className="font-semibold text-slate-300">Starting Location: </span>
                {startTripModalDuty.pickup_address}
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setStartTripModalDuty(null)}
                  className="rounded-xl border border-slate-800 px-4 py-2 text-sm font-medium text-slate-400 hover:bg-slate-800 hover:text-white transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={startTripMutation.isPending}
                  className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 transition disabled:opacity-50"
                >
                  {startTripMutation.isPending ? 'Starting...' : 'Confirm Trip Start'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Complete Trip */}
      {completeTripModalDuty && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
              <div>
                <h3 className="text-lg font-bold text-white">Complete Trip & Finalize Duty</h3>
                <p className="text-xs text-slate-400">
                  Duty <span className="font-mono text-indigo-400 font-semibold">{completeTripModalDuty.duty_number}</span>
                </p>
              </div>
              <button
                onClick={() => setCompleteTripModalDuty(null)}
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

            <form onSubmit={handleCompleteTripSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Ending Odometer (KM) * (Must be &ge; Starting Odometer)
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={completeForm.end_odometer}
                  onChange={(e) => setCompleteForm({ ...completeForm, end_odometer: e.target.value })}
                  className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Toll (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={completeForm.toll_amount}
                    onChange={(e) => setCompleteForm({ ...completeForm, toll_amount: e.target.value })}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Fuel (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={completeForm.fuel_amount}
                    onChange={(e) => setCompleteForm({ ...completeForm, fuel_amount: e.target.value })}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Parking (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={completeForm.parking_amount}
                    onChange={(e) => setCompleteForm({ ...completeForm, parking_amount: e.target.value })}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Trip Closing Notes</label>
                <textarea
                  rows={2}
                  placeholder="Gate pass number, POD remarks, delivery signature confirmation..."
                  value={completeForm.notes}
                  onChange={(e) => setCompleteForm({ ...completeForm, notes: e.target.value })}
                  className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white placeholder-slate-600 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setCompleteTripModalDuty(null)}
                  className="rounded-xl border border-slate-800 px-4 py-2 text-sm font-medium text-slate-400 hover:bg-slate-800 hover:text-white transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={completeTripMutation.isPending}
                  className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 transition disabled:opacity-50"
                >
                  {completeTripMutation.isPending ? 'Finalizing...' : 'Finalize Trip & Complete Duty'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

