import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  CalendarCheck,
  Plus,
  Search,
  AlertCircle,
  X,
  FileCheck,
  CheckCircle2,
  Clock,
  ArrowRight,
  Truck,
} from 'lucide-react';
import { apiClient } from '../../lib/api';
import type {
  Booking,
  BookingRequest,
  BookingRequestCreate,
  BookingType,
  BookingServiceType,
  Customer,
} from '../../types';

export function BookingsPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'bookings' | 'requests'>('bookings');
  const [search, setSearch] = useState('');
  const [isRequestModalOpen, setIsRequestModalOpen] = useState(false);
  const [isDutyModalOpen, setIsDutyModalOpen] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null);
  const [formError, setFormError] = useState('');

  // New Booking Request Form State
  const [requestForm, setRequestForm] = useState<BookingRequestCreate>({
    customer_id: '',
    booking_type: 'SPOT',
    service_type: 'CARGO',
    pickup_address: '',
    drop_address: '',
    pickup_datetime: new Date(Date.now() + 3600000).toISOString().slice(0, 16),
    cargo_info: { weight_kg: '', material: '' },
    special_instructions: '',
    estimated_pricing: '',
  });

  // Duty Form State
  const [dutyForm, setDutyForm] = useState({
    scheduled_start_time: '',
    scheduled_end_time: '',
    notes: '',
  });

  // Fetch Customers for selector
  const { data: customers } = useQuery({
    queryKey: ['customers'],
    queryFn: () => apiClient<Customer[]>('/api/v1/customers'),
  });

  // Fetch Bookings
  const { data: bookings, isLoading: isBookingsLoading } = useQuery({
    queryKey: ['bookings'],
    queryFn: () => apiClient<Booking[]>('/api/v1/bookings'),
    enabled: activeTab === 'bookings',
  });

  // Fetch Booking Requests
  const { data: bookingRequests, isLoading: isRequestsLoading } = useQuery({
    queryKey: ['booking-requests'],
    queryFn: () => apiClient<BookingRequest[]>('/api/v1/booking-requests'),
    enabled: activeTab === 'requests',
  });

  // Create Request Mutation
  const createRequestMutation = useMutation({
    mutationFn: (data: BookingRequestCreate) =>
      apiClient<BookingRequest>('/api/v1/booking-requests', {
        method: 'POST',
        body: JSON.stringify({
          ...data,
          pickup_datetime: new Date(data.pickup_datetime).toISOString(),
          estimated_pricing: data.estimated_pricing ? data.estimated_pricing : undefined,
        }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['booking-requests'] });
      setIsRequestModalOpen(false);
      setFormError('');
    },
    onError: (err: Error) => setFormError(err.message),
  });

  // Confirm Request Mutation
  const confirmRequestMutation = useMutation({
    mutationFn: (requestId: string) =>
      apiClient<Booking>(`/api/v1/booking-requests/${requestId}/confirm`, {
        method: 'POST',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['booking-requests'] });
      queryClient.invalidateQueries({ queryKey: ['bookings'] });
      setActiveTab('bookings');
    },
    onError: (err: Error) => alert(`Error confirming request: ${err.message}`),
  });

  // Submit Request Mutation
  const submitRequestMutation = useMutation({
    mutationFn: (requestId: string) =>
      apiClient<BookingRequest>(`/api/v1/booking-requests/${requestId}/submit`, {
        method: 'POST',
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['booking-requests'] }),
  });

  // Create Duty Mutation
  const createDutyMutation = useMutation({
    mutationFn: (bookingId: string) =>
      apiClient(`/api/v1/bookings/${bookingId}/create-duty`, {
        method: 'POST',
        body: JSON.stringify({
          scheduled_start_time: new Date(dutyForm.scheduled_start_time).toISOString(),
          scheduled_end_time: new Date(dutyForm.scheduled_end_time).toISOString(),
          notes: dutyForm.notes,
        }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['duties'] });
      setIsDutyModalOpen(false);
      setSelectedBooking(null);
      alert('Duty roster generated successfully! Proceed to Duties page to allocate Driver & Vehicle.');
    },
    onError: (err: Error) => setFormError(err.message),
  });

  const openDutyModal = (b: Booking) => {
    setSelectedBooking(b);
    const start = new Date(b.pickup_datetime).toISOString().slice(0, 16);
    const end = new Date(new Date(b.pickup_datetime).getTime() + 4 * 3600000).toISOString().slice(0, 16);
    setDutyForm({ scheduled_start_time: start, scheduled_end_time: end, notes: '' });
    setIsDutyModalOpen(true);
  };

  const filteredBookings = bookings?.filter((b) =>
    b.booking_number.toLowerCase().includes(search.toLowerCase()) ||
    b.pickup_address.toLowerCase().includes(search.toLowerCase()) ||
    b.drop_address.toLowerCase().includes(search.toLowerCase())
  );

  const filteredRequests = bookingRequests?.filter((r) =>
    r.request_number.toLowerCase().includes(search.toLowerCase()) ||
    r.pickup_address.toLowerCase().includes(search.toLowerCase()) ||
    r.drop_address.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Transport Bookings</h1>
          <p className="text-sm text-slate-400">Manage client booking requests and authoritative transport contracts.</p>
        </div>
        <button
          onClick={() => {
            setFormError('');
            setIsRequestModalOpen(true);
          }}
          className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition"
        >
          <Plus className="h-4 w-4" />
          New Booking Request
        </button>
      </div>

      {/* Tabs & Search */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex gap-2 p-1 rounded-xl bg-slate-900/60 border border-slate-800 w-fit">
          <button
            onClick={() => setActiveTab('bookings')}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${
              activeTab === 'bookings'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Authoritative Bookings
          </button>
          <button
            onClick={() => setActiveTab('requests')}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${
              activeTab === 'requests'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Booking Requests
          </button>
        </div>

        <div className="flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2 max-w-md w-full">
          <Search className="h-4 w-4 text-slate-500" />
          <input
            type="text"
            placeholder={`Search ${activeTab === 'bookings' ? 'bookings' : 'requests'} by number, address...`}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none w-full"
          />
        </div>
      </div>

      {/* Table: Bookings */}
      {activeTab === 'bookings' && (
        <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/40">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="border-b border-slate-800 bg-slate-950/80 text-xs font-semibold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="px-5 py-3.5">Booking #</th>
                <th className="px-5 py-3.5">Type & Service</th>
                <th className="px-5 py-3.5">Route</th>
                <th className="px-5 py-3.5">Pickup Date</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isBookingsLoading ? (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-slate-500">
                    Loading authoritative bookings...
                  </td>
                </tr>
              ) : filteredBookings?.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-slate-500">
                    <CalendarCheck className="mx-auto h-8 w-8 text-slate-600 mb-2" />
                    No confirmed transport bookings found.
                  </td>
                </tr>
              ) : (
                filteredBookings?.map((booking) => (
                  <tr key={booking.id} className="hover:bg-slate-800/30 transition">
                    <td className="px-5 py-4 font-mono font-medium text-white">
                      {booking.booking_number}
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-block rounded-md bg-slate-800 px-2 py-0.5 text-xs font-semibold text-slate-300 mr-2">
                        {booking.booking_type}
                      </span>
                      <span className="inline-block rounded-md bg-indigo-950/60 border border-indigo-800/40 px-2 py-0.5 text-xs font-semibold text-indigo-300">
                        {booking.service_type}
                      </span>
                    </td>
                    <td className="px-5 py-4 max-w-xs truncate">
                      <div className="flex items-center gap-1.5 text-slate-200">
                        <span className="truncate">{booking.pickup_address}</span>
                        <ArrowRight className="h-3 w-3 flex-shrink-0 text-slate-500" />
                        <span className="truncate text-slate-400">{booking.drop_address}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-slate-300">
                      {new Date(booking.pickup_datetime).toLocaleString()}
                    </td>
                    <td className="px-5 py-4">
                      <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                        booking.status === 'CONFIRMED'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : booking.status === 'IN_PROGRESS'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : booking.status === 'COMPLETED'
                          ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}>
                        {booking.status}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right">
                      {booking.status === 'CONFIRMED' && (
                        <button
                          onClick={() => openDutyModal(booking)}
                          className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600/20 border border-indigo-500/30 px-3 py-1.5 text-xs font-semibold text-indigo-300 hover:bg-indigo-600 hover:text-white transition"
                        >
                          <Truck className="h-3.5 w-3.5" />
                          Create Duty
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Table: Booking Requests */}
      {activeTab === 'requests' && (
        <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/40">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="border-b border-slate-800 bg-slate-950/80 text-xs font-semibold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="px-5 py-3.5">Request #</th>
                <th className="px-5 py-3.5">Type & Service</th>
                <th className="px-5 py-3.5">Route</th>
                <th className="px-5 py-3.5">Est. Price</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isRequestsLoading ? (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-slate-500">
                    Loading booking requests...
                  </td>
                </tr>
              ) : filteredRequests?.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-slate-500">
                    <FileCheck className="mx-auto h-8 w-8 text-slate-600 mb-2" />
                    No booking requests recorded.
                  </td>
                </tr>
              ) : (
                filteredRequests?.map((req) => (
                  <tr key={req.id} className="hover:bg-slate-800/30 transition">
                    <td className="px-5 py-4 font-mono font-medium text-white">
                      {req.request_number}
                    </td>
                    <td className="px-5 py-4">
                      <span className="inline-block rounded-md bg-slate-800 px-2 py-0.5 text-xs font-semibold text-slate-300 mr-2">
                        {req.booking_type}
                      </span>
                      <span className="inline-block rounded-md bg-indigo-950/60 border border-indigo-800/40 px-2 py-0.5 text-xs font-semibold text-indigo-300">
                        {req.service_type}
                      </span>
                    </td>
                    <td className="px-5 py-4 max-w-xs truncate">
                      <div className="flex items-center gap-1.5 text-slate-200">
                        <span className="truncate">{req.pickup_address}</span>
                        <ArrowRight className="h-3 w-3 flex-shrink-0 text-slate-500" />
                        <span className="truncate text-slate-400">{req.drop_address}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4 font-mono text-slate-300">
                      {req.estimated_pricing ? `₹${req.estimated_pricing}` : '—'}
                    </td>
                    <td className="px-5 py-4">
                      <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                        req.status === 'CONFIRMED'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : req.status === 'REQUESTED'
                          ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                          : req.status === 'DRAFT'
                          ? 'bg-slate-800 text-slate-400 border border-slate-700'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}>
                        {req.status}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right space-x-2">
                      {req.status === 'DRAFT' && (
                        <button
                          onClick={() => submitRequestMutation.mutate(req.id)}
                          disabled={submitRequestMutation.isPending}
                          className="inline-flex items-center gap-1 rounded-lg bg-slate-800 px-2.5 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 transition"
                        >
                          <Clock className="h-3.5 w-3.5" />
                          Submit
                        </button>
                      )}
                      {(req.status === 'DRAFT' || req.status === 'REQUESTED') && (
                        <button
                          onClick={() => confirmRequestMutation.mutate(req.id)}
                          disabled={confirmRequestMutation.isPending}
                          className="inline-flex items-center gap-1 rounded-lg bg-emerald-600/20 border border-emerald-500/30 px-3 py-1.5 text-xs font-semibold text-emerald-400 hover:bg-emerald-600 hover:text-white transition"
                        >
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Confirm Booking
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal: New Booking Request */}
      {isRequestModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-xl rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
              <div>
                <h3 className="text-lg font-bold text-white">Create Booking Request</h3>
                <p className="text-xs text-slate-400">Initialize a client trip request before confirmation.</p>
              </div>
              <button
                onClick={() => setIsRequestModalOpen(false)}
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

            <form onSubmit={(e) => { e.preventDefault(); createRequestMutation.mutate(requestForm); }} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Customer / Client *</label>
                <select
                  required
                  value={requestForm.customer_id}
                  onChange={(e) => setRequestForm({ ...requestForm, customer_id: e.target.value })}
                  className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                >
                  <option value="">Select a customer...</option>
                  {customers?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} {c.gstin ? `(${c.gstin})` : ''}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Booking Type</label>
                  <select
                    value={requestForm.booking_type}
                    onChange={(e) => setRequestForm({ ...requestForm, booking_type: e.target.value as BookingType })}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="SPOT">Spot / Ad-hoc</option>
                    <option value="CONTRACT">Contract / Dedicated</option>
                    <option value="LOCAL">Local City Run</option>
                    <option value="AIRPORT">Airport Transfer</option>
                    <option value="OUTSTATION">Outstation Intercity</option>
                    <option value="CORPORATE">Corporate Commute</option>
                    <option value="RENTAL">Package Rental</option>
                    <option value="ETS">ETS Shuttle</option>
                    <option value="FIXED">Fixed Route</option>
                    <option value="RECURRING">Recurring Schedule</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Service Type</label>
                  <select
                    value={requestForm.service_type}
                    onChange={(e) => setRequestForm({ ...requestForm, service_type: e.target.value as BookingServiceType })}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="CARGO">Cargo / Freight</option>
                    <option value="PASSENGER">Passenger Transit</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Pickup Address *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Warehouse 3, Bhiwandi Logistics Park, Maharashtra"
                  value={requestForm.pickup_address}
                  onChange={(e) => setRequestForm({ ...requestForm, pickup_address: e.target.value })}
                  className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white placeholder-slate-600 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Drop / Destination Address *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. JNPT Port Container Terminal 2, Navi Mumbai"
                  value={requestForm.drop_address}
                  onChange={(e) => setRequestForm({ ...requestForm, drop_address: e.target.value })}
                  className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white placeholder-slate-600 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Pickup Date & Time *</label>
                  <input
                    type="datetime-local"
                    required
                    value={requestForm.pickup_datetime}
                    onChange={(e) => setRequestForm({ ...requestForm, pickup_datetime: e.target.value })}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Estimated Pricing (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="e.g. 18500.00"
                    value={requestForm.estimated_pricing}
                    onChange={(e) => setRequestForm({ ...requestForm, estimated_pricing: e.target.value })}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white placeholder-slate-600 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsRequestModalOpen(false)}
                  className="rounded-xl border border-slate-800 px-4 py-2 text-sm font-medium text-slate-400 hover:bg-slate-800 hover:text-white transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createRequestMutation.isPending}
                  className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 transition disabled:opacity-50"
                >
                  {createRequestMutation.isPending ? 'Creating...' : 'Create Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Generate Duty from Booking */}
      {isDutyModalOpen && selectedBooking && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
              <div>
                <h3 className="text-lg font-bold text-white">Generate Duty Roster</h3>
                <p className="text-xs text-slate-400">
                  Creating operational duty for Booking <span className="font-mono text-indigo-400 font-semibold">{selectedBooking.booking_number}</span>
                </p>
              </div>
              <button
                onClick={() => setIsDutyModalOpen(false)}
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
                createDutyMutation.mutate(selectedBooking.id);
              }}
              className="space-y-4"
            >
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Scheduled Start *</label>
                  <input
                    type="datetime-local"
                    required
                    value={dutyForm.scheduled_start_time}
                    onChange={(e) => setDutyForm({ ...dutyForm, scheduled_start_time: e.target.value })}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Scheduled End *</label>
                  <input
                    type="datetime-local"
                    required
                    value={dutyForm.scheduled_end_time}
                    onChange={(e) => setDutyForm({ ...dutyForm, scheduled_end_time: e.target.value })}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Duty Notes / Special Instructions</label>
                <textarea
                  rows={3}
                  placeholder="Special instructions for driver, cargo handling instructions, or client gate pass requirements..."
                  value={dutyForm.notes}
                  onChange={(e) => setDutyForm({ ...dutyForm, notes: e.target.value })}
                  className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-white placeholder-slate-600 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsDutyModalOpen(false)}
                  className="rounded-xl border border-slate-800 px-4 py-2 text-sm font-medium text-slate-400 hover:bg-slate-800 hover:text-white transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createDutyMutation.isPending}
                  className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 transition disabled:opacity-50"
                >
                  {createDutyMutation.isPending ? 'Generating...' : 'Confirm & Generate Duty'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

