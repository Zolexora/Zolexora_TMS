import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  Truck,
  LayoutDashboard,
  CalendarCheck,
  ClipboardList,
  Radio,
  Users,
  Building2,
  FileText,
  CreditCard,
  Receipt,
  Settings,
  LogOut,
  Shield,
  Crown,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '../features/auth/useAuth';

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
}

const navigation: { section: string; items: NavItem[] }[] = [
  {
    section: 'Operations',
    items: [
      { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
      { name: 'Bookings', href: '/bookings', icon: CalendarCheck },
      { name: 'Duties', href: '/duties', icon: ClipboardList },
      { name: 'Dispatch Board', href: '/dispatch', icon: Radio },
      { name: 'Rate Cards', href: '/rate-cards', icon: FileText },
    ],
  },
  {
    section: 'Compliance & Fleet',
    items: [
      { name: 'Dashboard', href: '/compliance', icon: Shield },
      { name: 'Customers', href: '/compliance/customers', icon: Building2 },
      { name: 'Vendors', href: '/compliance/vendors', icon: Building2 },
      { name: 'Fleet Vehicles', href: '/compliance/vehicles', icon: Truck },
      { name: 'Drivers', href: '/compliance/drivers', icon: Users },
    ],
  },
  {
    section: 'Billing',
    items: [
      { name: 'Billing', href: '/billing', icon: FileText },
      { name: 'Invoices', href: '/invoices', icon: FileText },
      { name: 'Customer Payments', href: '/payments', icon: CreditCard },
      { name: 'Receivables', href: '/receivables', icon: CreditCard },
    ],
  },
  {
    section: 'Vendor Payments',
    items: [
      { name: 'Payables', href: '/payables', icon: Receipt },
      { name: 'Vendor Settlements', href: '/vendor-settlements', icon: Receipt },
      { name: 'Payment History', href: '/vendor-payments', icon: CreditCard },
    ],
  },
  {
    section: 'Finances',
    items: [
      { name: 'Expenses', href: '/expenses', icon: Receipt },
      { name: 'Profit & Loss', href: '/reports/pnl', icon: FileText },
      { name: 'Financial Periods', href: '/financial-periods', icon: FileText },
    ],
  },
  {
    section: 'Administration',
    items: [
      { name: 'Workspace & RBAC', href: '/settings', icon: Settings },
    ],
  },
];

export function DashboardLayout() {
  const { user, authMe, organisation, isCommander, signOut } = useAuth();
  const navigate = useNavigate();

  const handleSignOut = async () => {
    await signOut();
    navigate('/login');
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 antialiased">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-800/80 bg-slate-900/90 backdrop-blur-xl">
        {/* Brand Header */}
        <div className="flex h-16 items-center gap-3 border-b border-slate-800/80 px-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-lg shadow-indigo-600/30">
            <Truck className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <span className="font-bold tracking-tight text-white text-base">Zolexora TMS</span>
            <span className="text-[10px] font-medium uppercase tracking-widest text-indigo-400">Transport Hub</span>
          </div>
        </div>

        {/* Organisation Context Card */}
        <div className="p-4 border-b border-slate-800/60">
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300 truncate max-w-[140px]">
                {organisation?.name || 'Loading Workspace...'}
              </span>
              {isCommander ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-semibold text-amber-400 border border-amber-500/30">
                  <Crown className="h-3 w-3" />
                  Commander
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 rounded-full bg-indigo-500/10 px-2 py-0.5 text-[10px] font-semibold text-indigo-400 border border-indigo-500/30">
                  <Shield className="h-3 w-3" />
                  {authMe?.role_code || 'Member'}
                </span>
              )}
            </div>
            <div className="mt-1 flex items-center justify-between text-[11px] text-slate-500">
              <span className="truncate">{organisation?.organisation_type || 'Transport Org'}</span>
              <span className="font-mono text-[9px] text-slate-600">ID: {organisation?.id ? organisation.id.substring(0, 6) : '---'}</span>
            </div>
          </div>
        </div>

        {/* Navigation Sections */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          {navigation.map((group) => (
            <div key={group.section} className="space-y-1">
              <p className="px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                {group.section}
              </p>
              <div className="mt-2 space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.name}
                      to={item.href}
                      className={({ isActive }) =>
                        `group flex items-center justify-between rounded-lg px-3 py-2 text-sm font-medium transition ${
                          isActive
                            ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                            : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                        }`
                      }
                    >
                      <div className="flex items-center gap-3">
                        <Icon className="h-4 w-4 shrink-0" />
                        <span>{item.name}</span>
                      </div>
                      <ChevronRight className="h-3.5 w-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* User Footer */}
        <div className="border-t border-slate-800/80 p-3">
          <div className="flex items-center justify-between rounded-lg bg-slate-950/40 p-2 border border-slate-800/60">
            <div className="flex flex-col truncate pr-2">
              <span className="text-xs font-medium text-slate-200 truncate">
                {user?.email || 'Authenticated User'}
              </span>
              <span className="text-[10px] text-slate-500">Production Tenant</span>
            </div>
            <button
              onClick={handleSignOut}
              title="Sign Out"
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-red-400 transition"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="pl-64 flex flex-1 flex-col min-w-0">
        {/* Top bar */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-800/80 bg-slate-950/80 px-8 backdrop-blur-md">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span>Workspace</span>
            <span>/</span>
            <span className="font-semibold text-slate-200">{organisation?.name || 'Zolexora TMS'}</span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              API Connected: Render
            </div>

            {isCommander && (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-300">
                <Crown className="h-3.5 w-3.5" />
                Commander Authority Active
              </span>
            )}
          </div>
        </header>

        {/* Page Body */}
        <main className="flex-1 p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
