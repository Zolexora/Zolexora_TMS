import {
  Truck,
  CalendarCheck,
  ClipboardList,
  Radio,
  Users,
  ShieldCheck,
  TrendingUp,
  AlertCircle,
  Plus,
} from 'lucide-react';
import { useAuth } from '../auth/useAuth';
import { Link } from 'react-router-dom';

export function DashboardPage() {
  const { organisation, authMe, isCommander } = useAuth();

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-indigo-500/20 bg-gradient-to-r from-indigo-950/60 via-slate-900/60 to-slate-900/60 p-8 shadow-xl">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-indigo-500/20 px-3 py-1 text-xs font-semibold text-indigo-400 border border-indigo-500/30">
                Workspace Active
              </span>
              {isCommander && (
                <span className="rounded-full bg-amber-500/20 px-3 py-1 text-xs font-semibold text-amber-300 border border-amber-500/30">
                  Commander Clearance
                </span>
              )}
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-white">
              {organisation?.name || 'Transport Operations Control'}
            </h1>
            <p className="max-w-2xl text-sm text-slate-400">
              Welcome to your dedicated Zolexora TMS control tower. Track duty rosters, fleet assignments, authoritative billing, and real-time dispatch.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/bookings"
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition"
            >
              <Plus className="h-4 w-4" />
              New Booking
            </Link>
            <Link
              to="/dispatch"
              className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800/80 px-4 py-2.5 text-sm font-semibold text-slate-200 hover:bg-slate-700 transition"
            >
              <Radio className="h-4 w-4 text-emerald-400" />
              Dispatch Tower
            </Link>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Active Duties</span>
            <div className="rounded-lg bg-indigo-500/10 p-2 text-indigo-400">
              <ClipboardList className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4">
            <span className="text-3xl font-bold text-white">0</span>
            <span className="ml-2 text-xs text-slate-500">scheduled today</span>
          </div>
          <div className="mt-2 flex items-center text-xs text-indigo-400">
            <span>Ready for dispatch allocation</span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">In-Transit Trips</span>
            <div className="rounded-lg bg-emerald-500/10 p-2 text-emerald-400">
              <Radio className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4">
            <span className="text-3xl font-bold text-white">0</span>
            <span className="ml-2 text-xs text-slate-500">live on road</span>
          </div>
          <div className="mt-2 flex items-center text-xs text-emerald-400">
            <span>Real-time GPS tracking ready</span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Fleet Assets</span>
            <div className="rounded-lg bg-cyan-500/10 p-2 text-cyan-400">
              <Truck className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4">
            <span className="text-3xl font-bold text-white">0</span>
            <span className="ml-2 text-xs text-slate-500">vehicles registered</span>
          </div>
          <div className="mt-2 flex items-center text-xs text-cyan-400">
            <span>Fleet master data active</span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Active Drivers</span>
            <div className="rounded-lg bg-purple-500/10 p-2 text-purple-400">
              <Users className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4">
            <span className="text-3xl font-bold text-white">0</span>
            <span className="ml-2 text-xs text-slate-500">verified roster</span>
          </div>
          <div className="mt-2 flex items-center text-xs text-purple-400">
            <span>License and KYC compliance</span>
          </div>
        </div>
      </div>

      {/* Operational Modules & Quick Start */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Core Workflow Guide */}
        <div className="lg:col-span-2 rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
          <h2 className="text-lg font-bold text-white">Transport Operational Lifecycle</h2>
          <p className="text-xs text-slate-400 mt-1">
            Zolexora TMS orchestrates every transport stage with strict isolation and state machines.
          </p>

          <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">Stage 1</span>
                <CalendarCheck className="h-4 w-4 text-slate-400" />
              </div>
              <h3 className="mt-2 text-sm font-semibold text-white">Booking & Duty Scheduling</h3>
              <p className="mt-1 text-xs text-slate-400">
                Log customer booking requests with pickup/drop locations, package dimensions, or passenger details. Convert to actionable transport duties.
              </p>
            </div>

            <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">Stage 2</span>
                <Radio className="h-4 w-4 text-slate-400" />
              </div>
              <h3 className="mt-2 text-sm font-semibold text-white">Dispatch & Trip Execution</h3>
              <p className="mt-1 text-xs text-slate-400">
                Assign qualified drivers and compliant vehicles. Drivers accept via mobile web view; start trip with starting odometer and GPS check-in.
              </p>
            </div>

            <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">Stage 3</span>
                <ShieldCheck className="h-4 w-4 text-slate-400" />
              </div>
              <h3 className="mt-2 text-sm font-semibold text-white">Closing & Trip Expenses</h3>
              <p className="mt-1 text-xs text-slate-400">
                Record end odometer, fuel receipts, toll tickets, and driver allowances. Verify delivery proof (POD) before closing duty.
              </p>
            </div>

            <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">Stage 4</span>
                <TrendingUp className="h-4 w-4 text-slate-400" />
              </div>
              <h3 className="mt-2 text-sm font-semibold text-white">Billing, Invoice & Cashfree</h3>
              <p className="mt-1 text-xs text-slate-400">
                Authoritative billing engine computes base, slab KM, waiting hours, and GST. Auto-generate PDF invoices and Cashfree payment links.
              </p>
            </div>
          </div>
        </div>

        {/* Tenant Details & Status */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 space-y-6">
          <div>
            <h2 className="text-lg font-bold text-white">Workspace Security</h2>
            <p className="text-xs text-slate-400 mt-1">Tenant Isolation & Integrity</p>
          </div>

          <div className="space-y-4 text-sm">
            <div className="flex justify-between border-b border-slate-800/80 pb-2">
              <span className="text-slate-400">Tenant Status</span>
              <span className="font-semibold text-emerald-400">{organisation?.status || 'ACTIVE'}</span>
            </div>
            <div className="flex justify-between border-b border-slate-800/80 pb-2">
              <span className="text-slate-400">Entity Type</span>
              <span className="font-medium text-slate-200 truncate max-w-[160px]">
                {organisation?.organisation_type || '---'}
              </span>
            </div>
            <div className="flex justify-between border-b border-slate-800/80 pb-2">
              <span className="text-slate-400">Assigned Role</span>
              <span className="font-semibold text-amber-300">{authMe?.role_code || 'MEMBER'}</span>
            </div>
            <div className="flex justify-between border-b border-slate-800/80 pb-2">
              <span className="text-slate-400">Permissions</span>
              <span className="font-mono text-xs text-indigo-400">
                {authMe?.permissions?.length || 0} granted
              </span>
            </div>
          </div>

          <div className="rounded-xl bg-slate-950/60 p-4 border border-slate-800">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
              <AlertCircle className="h-4 w-4 text-indigo-400" />
              Tenant Isolation Boundary
            </div>
            <p className="mt-2 text-[11px] text-slate-400 leading-relaxed">
              All fleet data, customer details, duty dispatches, and financial ledgers are cryptographically and relationally bound to tenant <code className="text-indigo-400 font-mono">{organisation?.id ? organisation.id.substring(0, 8) : '...'}</code>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
