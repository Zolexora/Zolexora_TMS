import React, { useState } from 'react';
import { useAuth } from '../features/auth/hooks/useAuth';
import { useCompany } from '../features/companies/context/CompanyContext';
import { useTheme } from '../app/ThemeProvider';
import { useRouter, RoutePath } from '../app/router';
import { ROUTE_ROLES } from '../app/route-permissions';
import { usePeriod } from '../features/periods/context/PeriodContext';
import {
  LayoutDashboard, Building2, CalendarRange, FolderTree, Landmark,
  BookOpen, History, Upload, FileBarChart, Layers, ShieldAlert, Settings as SettingsIcon,
  Sun, Moon, LogOut, Menu, X, PanelLeftOpen, PanelLeftClose,
} from 'lucide-react';

interface SidebarItem {
  name: string;
  path: RoutePath;
  icon: React.ComponentType<any>;
}

interface SidebarSection {
  title: string;
  items: SidebarItem[];
}

export const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout } = useAuth();
  const { companies, activeCompany, setActiveCompany } = useCompany();
  const { theme, toggleTheme } = useTheme();
  const { path, navigate } = useRouter();
  const { years, periods, activeYear, activePeriod, setActiveYear, setActivePeriod } = usePeriod();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true);

  const navigationSections: SidebarSection[] = [
    {
      title: 'Overview',
      items: [
        { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
      ],
    },
    {
      title: 'Masters',
      items: [
        { name: 'Companies', path: '/companies', icon: Building2 },
        { name: 'Financial Periods', path: '/periods', icon: CalendarRange },
        { name: 'P&L Groups Tree', path: '/groups', icon: FolderTree },
        { name: 'Chart of Accounts', path: '/accounts', icon: Landmark },
      ],
    },
    {
      title: 'Operations',
      items: [
        { name: 'Manual Journal Entry', path: '/manual-entry', icon: BookOpen },
        { name: 'Journal History', path: '/entry-history', icon: History },
        { name: 'Bulk Import Accounts', path: '/bulk-upload', icon: Upload },
        { name: 'Import History Logs', path: '/import-history', icon: History },
        { name: 'P&L Statements', path: '/reports', icon: FileBarChart },
        { name: 'Company Comparison', path: '/comparison', icon: Layers },
        { name: 'Audit Logs Trail', path: '/audit-logs', icon: ShieldAlert },
        { name: 'Settings', path: '/settings', icon: SettingsIcon },
      ],
    },
  ];

  const filteredNavigationSections = navigationSections
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => {
        if (user?.role === 'Admin') return true;
        return ROUTE_ROLES[item.path]?.includes(user?.role || 'Viewer') ?? true;
      }),
    }))
    .filter((section) => section.items.length > 0);

  const renderDesktopItem = (item: SidebarItem) => {
    const isActive = path === item.path;
    return (
      <button
        key={item.name}
        onClick={() => navigate(item.path)}
        aria-label={item.name}
        title={sidebarCollapsed ? item.name : undefined}
        className={`group flex w-full items-center rounded-xl py-2.5 text-sm font-medium transition-all duration-150 ${
          sidebarCollapsed ? 'justify-center px-2' : 'px-4'
        } ${
          isActive
            ? 'bg-indigo-600 text-white font-semibold shadow-md shadow-indigo-500/20'
            : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100/50 dark:hover:bg-slate-800/50 hover:text-slate-900 dark:hover:text-slate-100'
        }`}
      >
        <item.icon className={`${sidebarCollapsed ? '' : 'mr-3'} h-5 w-5 flex-shrink-0 ${
          isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300'
        }`} />
        {!sidebarCollapsed && item.name}
      </button>
    );
  };

  const renderMobileItem = (item: SidebarItem) => {
    const isActive = path === item.path;
    return (
      <button
        key={item.name}
        onClick={() => { navigate(item.path); setSidebarOpen(false); }}
        className={`group flex w-full items-center rounded-xl px-4 py-3 text-sm font-medium transition-all duration-150 ${
          isActive
            ? 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-semibold'
            : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/50 hover:text-slate-900 dark:hover:text-slate-100'
        }`}
      >
        <item.icon className="mr-3 h-5 w-5 flex-shrink-0" />
        {item.name}
      </button>
    );
  };

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-800 transition-colors duration-200 dark:bg-slate-950 dark:text-slate-100">
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden" role="dialog" aria-modal="true">
          <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
          <div className="relative flex w-full max-w-xs flex-1 flex-col border-r border-slate-200/50 bg-white pt-5 pb-4 dark:border-slate-800/50 dark:bg-slate-900">
            <div className="absolute top-0 right-0 -mr-12 pt-2">
              <button onClick={() => setSidebarOpen(false)} className="ml-1 flex h-10 w-10 items-center justify-center rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500">
                <span className="sr-only">Close navigation</span>
                <X className="h-6 w-6 text-white" />
              </button>
            </div>
            <div className="flex flex-shrink-0 items-center px-6">
              <span className="text-xl font-bold tracking-tight text-indigo-600 dark:text-indigo-400">ZolexoraERP Lite</span>
            </div>
            <div className="mt-5 h-0 flex-1 overflow-y-auto px-4">
              <nav className="space-y-4">
                {filteredNavigationSections.map((section) => (
                  <div key={section.title} className="space-y-2">
                    <div className="px-4 text-[10px] font-bold uppercase tracking-[0.22em] text-slate-400 dark:text-slate-500">
                      {section.title}
                    </div>
                    <div className="space-y-1">
                      {section.items.map(renderMobileItem)}
                    </div>
                  </div>
                ))}
              </nav>
            </div>
          </div>
        </div>
      )}

      <div className={`hidden md:flex ${sidebarCollapsed ? 'md:w-20' : 'md:w-64'} md:fixed md:inset-y-0 md:flex-col border-r border-slate-200/50 bg-white/70 backdrop-blur-md transition-[width] duration-200 dark:border-slate-800/50 dark:bg-slate-900/70`}>
        <div className="flex flex-grow flex-col overflow-y-auto pt-5">
          <div className={`mb-8 flex flex-shrink-0 items-center ${sidebarCollapsed ? 'flex-col justify-center gap-2 px-2' : 'justify-between px-4'}`}>
            <span className="bg-gradient-to-r from-indigo-500 to-purple-500 bg-clip-text text-xl font-black tracking-wider text-transparent">
              {sidebarCollapsed ? 'Z' : <>ZOLEXORA<span className="text-slate-400 dark:text-slate-600">_ERP</span></>}
            </span>
            <button
              onClick={() => setSidebarCollapsed((collapsed) => !collapsed)}
              aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-indigo-500/10 hover:text-indigo-600"
            >
              {sidebarCollapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
            </button>
          </div>

          <div className={`flex-grow flex flex-col ${sidebarCollapsed ? 'px-2' : 'px-4'}`}>
            <nav className="flex-1 space-y-4 pb-4">
              {filteredNavigationSections.map((section) => (
                <div key={section.title} className="space-y-2">
                  {!sidebarCollapsed && (
                    <div className="px-3 pt-3 text-[10px] font-bold uppercase tracking-[0.22em] text-slate-400 dark:text-slate-500">
                      {section.title}
                    </div>
                  )}
                  <div className="space-y-1">
                    {section.items.map(renderDesktopItem)}
                  </div>
                </div>
              ))}
            </nav>
          </div>
        </div>
      </div>

      <div className={`${sidebarCollapsed ? 'md:pl-20' : 'md:pl-64'} flex w-full flex-1 flex-col transition-[padding] duration-200`}>
        <header className="sticky top-0 z-10 flex h-16 flex-shrink-0 justify-between border-b border-slate-200/50 bg-white/80 px-4 backdrop-blur-md dark:border-slate-800/50 dark:bg-slate-900/80 md:px-6">
          <div className="flex items-center">
            <button
              onClick={() => setSidebarOpen(true)}
              aria-label="Open navigation"
              className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 focus:outline-none dark:hover:bg-slate-800 dark:hover:text-slate-300 md:hidden"
            >
              <Menu className="h-6 w-6" />
            </button>

            <div className="ml-4 flex items-center md:ml-0">
              <span className="mr-2 hidden text-xs font-semibold uppercase tracking-wider text-slate-400 sm:inline-block">Scope:</span>
              <select
                value={activeCompany?.code || ''}
                onChange={(e) => {
                  const company = companies.find((c) => c.code === e.target.value);
                  setActiveCompany(company || null);
                }}
                className="cursor-pointer rounded-xl border-0 bg-slate-100 px-3 py-1.5 text-sm font-semibold focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800"
              >
                {companies.length === 0 ? (
                  <option value="">No Companies Found</option>
                ) : (
                  companies.map((c) => (
                    <option key={c.code} value={c.code}>
                      {c.name} ({c.code})
                    </option>
                  ))
                )}
              </select>
            </div>

            <div className="ml-3 hidden items-center space-x-2 lg:flex">
              <select
                aria-label="Financial year"
                value={activeYear?.id || ''}
                onChange={(event) => setActiveYear(years.find((year) => year.id === event.target.value) || null)}
                className="rounded-xl border-0 bg-slate-100 px-3 py-1.5 text-sm font-semibold focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800"
              >
                <option value="">No financial year</option>
                {years.map((year) => <option key={year.id} value={year.id}>{year.name}</option>)}
              </select>
              <select
                aria-label="Financial month"
                value={activePeriod?.id || ''}
                onChange={(event) => setActivePeriod(periods.find((period) => period.id === event.target.value) || null)}
                className="rounded-xl border-0 bg-slate-100 px-3 py-1.5 text-sm font-semibold focus:ring-2 focus:ring-indigo-500 dark:bg-slate-800"
              >
                <option value="">No period</option>
                {periods.map((period) => <option key={period.id} value={period.id}>{period.period_code}</option>)}
              </select>
              {activePeriod && (
                <span
                  className={`rounded-full px-2 py-1 text-2xs font-bold uppercase ${
                    activePeriod.status === 'open'
                      ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400'
                      : activePeriod.status === 'closed'
                        ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400'
                        : 'bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-400'
                  }`}
                >
                  {activePeriod.status}
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={toggleTheme}
              aria-label={theme === 'dark' ? 'Use light theme' : 'Use dark theme'}
              className="rounded-xl p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-300"
              title="Toggle Theme Mode"
            >
              {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>

            <div className="flex items-center space-x-2 border-l border-slate-200 pl-3 dark:border-slate-800">
              <div className="hidden text-right lg:block">
                <p className="text-xs font-medium text-slate-900 dark:text-slate-100">{user?.email}</p>
                <span className="inline-flex items-center rounded-full bg-indigo-500/10 px-2 py-0.5 text-[10px] font-semibold text-indigo-600 dark:text-indigo-400">
                  {user?.role}
                </span>
              </div>
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-sm font-bold uppercase text-white shadow-sm shadow-indigo-500/20">
                {user?.email?.[0] || 'U'}
              </div>
              <button
                onClick={logout}
                aria-label="Log out"
                className="rounded-xl p-2 text-red-500 transition-colors hover:bg-red-500/10 hover:text-red-700 dark:hover:bg-red-500/20"
                title="Log Out"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          {children}
        </main>
      </div>
    </div>
  );
};
