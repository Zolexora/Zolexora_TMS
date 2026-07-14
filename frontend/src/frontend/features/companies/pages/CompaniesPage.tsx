import React, { useState } from 'react';
import { useCompany } from '../context/CompanyContext';
import { api } from '../../../api/client';
import { Plus, Edit2, X, AlertCircle, Power } from 'lucide-react';
import { Company } from '../../../../shared/types';

export const CompaniesPage: React.FC = () => {
  const { companies, refreshCompanies } = useCompany();
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [editingCompany, setEditingCompany] = useState<Company | null>(null);
  
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [currency, setCurrency] = useState('INR');
  const [fiscalYearStart, setFiscalYearStart] = useState('04-01');
  const [legalName, setLegalName] = useState('');
  const [businessType, setBusinessType] = useState('');
  const [gstNumber, setGstNumber] = useState('');
  const [panNumber, setPanNumber] = useState('');
  const [registeredAddress, setRegisteredAddress] = useState('');
  const [logoObjectKey, setLogoObjectKey] = useState('');
  const [sites, setSites] = useState<Array<{ site_code: string; site_name: string; address: string }>>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const resetForm = () => {
    setCode('');
    setName('');
    setCurrency('INR');
    setFiscalYearStart('04-01');
    setLegalName('');
    setBusinessType('');
    setGstNumber('');
    setPanNumber('');
    setRegisteredAddress('');
    setLogoObjectKey('');
    setSites([]);
    setError(null);
  };

  const validateInput = () => {
    if (!name.trim()) {
      setError('Company name is required.');
      return false;
    }
    if (!/^(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/.test(fiscalYearStart)) {
      setError('Fiscal Year Start must be in MM-DD format.');
      return false;
    }
    const siteCodes = new Set<string>();
    for (const [index, site] of sites.entries()) {
      const normalizedCode = site.site_code.trim().toUpperCase();
      if (!normalizedCode || !site.site_name.trim()) {
        setError(`Site ${index + 1} requires both a code and name.`);
        return false;
      }
      if (!/^[A-Z0-9_-]+$/.test(normalizedCode)) {
        setError(`Site ${index + 1} code may contain letters, numbers, underscores, and hyphens only.`);
        return false;
      }
      if (siteCodes.has(normalizedCode)) {
        setError('Site codes must be unique within the company.');
        return false;
      }
      siteCodes.add(normalizedCode);
    }
    return true;
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim()) {
      setError('Company code is required.');
      return;
    }
    if (!/^[a-zA-Z0-9-]+$/.test(code)) {
      setError('Company code must be alphanumeric or contain hyphens only.');
      return;
    }
    if (code.length > 100) {
      setError('Company code length cannot exceed 100 characters.');
      return;
    }
    if (!validateInput()) return;

    setLoading(true);
    try {
      setError(null);
      await api.post('/companies', {
        code: code.trim(),
        name: name.trim(),
        currency,
        fiscal_year_start: fiscalYearStart,
        legal_name: legalName.trim() || name.trim(),
        business_type: businessType.trim() || null,
        gst_number: gstNumber.trim() || null,
        pan_number: panNumber.trim() || null,
        registered_address: registeredAddress.trim() || null,
        logo_object_key: logoObjectKey.trim() || null,
        sites: sites.map((site) => ({ site_code: site.site_code.trim().toUpperCase(), site_name: site.site_name.trim(), address: site.address.trim() || null })),
      });
      await refreshCompanies();
      setIsAddOpen(false);
      resetForm();
    } catch (err: any) {
      setError(err.message || 'Failed to create company.');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingCompany) return;
    if (!validateInput()) return;

    setLoading(true);
    try {
      setError(null);
      await api.put(`/companies/${editingCompany.code}`, {
        name: name.trim(),
        currency,
        fiscal_year_start: fiscalYearStart,
        legal_name: legalName.trim() || name.trim(),
        business_type: businessType.trim() || null,
        gst_number: gstNumber.trim() || null,
        pan_number: panNumber.trim() || null,
        registered_address: registeredAddress.trim() || null,
        logo_object_key: logoObjectKey.trim() || null,
      });
      await refreshCompanies();
      setEditingCompany(null);
      resetForm();
    } catch (err: any) {
      setError(err.message || 'Failed to update company.');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (company: Company) => {
    const nextActive = !company.is_active;
    if (!window.confirm(`${nextActive ? 'Reactivate' : 'Deactivate'} ${company.name}? Historical reports remain available.`)) return;
    setLoading(true);
    try {
      setError(null);
      if (nextActive) await api.patch(`/companies/${company.code}`, { is_active: true });
      else await api.delete(`/companies/${company.code}`);
      await refreshCompanies();
    } catch (err: any) {
      setError(err.message || 'Failed to change company status.');
    } finally {
      setLoading(false);
    }
  };

  const extendedFields = (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-1">
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Legal Name</label>
          <input value={legalName} onChange={(e) => setLegalName(e.target.value)} placeholder="Registered legal name"
            className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800" disabled={loading} />
        </div>
        <div className="space-y-1">
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Business Type</label>
          <input value={businessType} onChange={(e) => setBusinessType(e.target.value)} placeholder="Transport, hospitality, dairy…"
            className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800" disabled={loading} />
        </div>
        <div className="space-y-1">
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">GST Number</label>
          <input value={gstNumber} onChange={(e) => setGstNumber(e.target.value)} placeholder="Optional"
            className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800" disabled={loading} />
        </div>
        <div className="space-y-1">
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">PAN Number</label>
          <input value={panNumber} onChange={(e) => setPanNumber(e.target.value)} placeholder="Optional"
            className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800" disabled={loading} />
        </div>
      </div>
      <div className="space-y-1">
        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Registered Address</label>
        <textarea value={registeredAddress} onChange={(e) => setRegisteredAddress(e.target.value)} rows={2} placeholder="Optional"
          className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800" disabled={loading} />
      </div>
      <div className="space-y-1">
        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Logo R2 Object Key</label>
        <input value={logoObjectKey} onChange={(e) => setLogoObjectKey(e.target.value)} placeholder="company-logos/example.png"
          className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 font-mono text-sm" disabled={loading} />
      </div>
    </>
  );

  const siteFields = (
    <div className="space-y-3 rounded-xl border border-slate-200 dark:border-slate-800 p-4">
      <div className="flex items-center justify-between gap-3">
        <div><p className="text-sm font-bold">Sites</p><p className="text-xs text-slate-500">Optional operating locations created with this company.</p></div>
        <button type="button" onClick={() => setSites((current) => [...current, { site_code: '', site_name: '', address: '' }])}
          className="inline-flex items-center gap-1 rounded-lg bg-indigo-500/10 px-3 py-2 text-xs font-semibold text-indigo-600">
          <Plus className="h-3.5 w-3.5" /> Add site
        </button>
      </div>
      {sites.length === 0 ? <p className="text-xs text-slate-400">No sites added.</p> : sites.map((site, index) => (
        <div key={index} className="grid grid-cols-1 sm:grid-cols-[1fr_1.4fr_1.6fr_auto] gap-2 items-end">
          <label className="text-xs font-semibold text-slate-500">Code
            <input value={site.site_code} onChange={(e) => setSites((current) => current.map((row, rowIndex) => rowIndex === index ? { ...row, site_code: e.target.value } : row))}
              placeholder="SITE_01" className="mt-1 w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 px-3 py-2" />
          </label>
          <label className="text-xs font-semibold text-slate-500">Site name
            <input value={site.site_name} onChange={(e) => setSites((current) => current.map((row, rowIndex) => rowIndex === index ? { ...row, site_name: e.target.value } : row))}
              placeholder="Main Site" className="mt-1 w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 px-3 py-2" />
          </label>
          <label className="text-xs font-semibold text-slate-500">Address
            <input value={site.address} onChange={(e) => setSites((current) => current.map((row, rowIndex) => rowIndex === index ? { ...row, address: e.target.value } : row))}
              placeholder="Optional" className="mt-1 w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 px-3 py-2" />
          </label>
          <button type="button" aria-label={`Remove site ${index + 1}`} onClick={() => setSites((current) => current.filter((_, rowIndex) => rowIndex !== index))}
            className="rounded-lg p-2 text-red-500 hover:bg-red-500/10"><X className="h-4 w-4" /></button>
        </div>
      ))}
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center space-y-4 sm:space-y-0">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-800 dark:text-slate-100">Companies Management</h2>
          <p className="text-slate-500 dark:text-slate-400">Add or modify operating legal entities in your ledger workspace.</p>
        </div>
        <button
          onClick={() => {
            resetForm();
            setIsAddOpen(true);
          }}
          className="flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-xl transition-all shadow-md shadow-indigo-500/10 self-start sm:self-auto font-medium"
        >
          <Plus className="h-4 w-4" />
          <span>Add Company</span>
        </button>
      </div>

      <div className="bg-white dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-850 backdrop-blur-md rounded-2xl shadow-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
            <thead className="bg-slate-50 dark:bg-slate-950/50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Code</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Currency</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Fiscal Start (MM-DD)</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {companies.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-400 dark:text-slate-500">
                    No companies configured. Click "Add Company" to begin.
                  </td>
                </tr>
              ) : (
                companies.map((comp) => (
                  <tr key={comp.code} className="hover:bg-slate-50/50 dark:hover:bg-slate-850/20 transition-colors">
                    <td className="px-6 py-4 font-mono text-sm text-indigo-600 dark:text-indigo-400 font-semibold">{comp.code}</td>
                    <td className="px-6 py-4 text-sm font-semibold text-slate-800 dark:text-slate-200">{comp.name}</td>
                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">{comp.currency}</td>
                    <td className="px-6 py-4 text-sm font-mono text-slate-600 dark:text-slate-400">{comp.fiscal_year_start}</td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${comp.is_active === false ? 'bg-slate-200 text-slate-600 dark:bg-slate-800 dark:text-slate-300' : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'}`}>
                        {comp.is_active === false ? 'Inactive' : 'Active'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right text-sm">
                      <button
                        onClick={() => {
                          setEditingCompany(comp);
                          setCode(comp.code);
                          setName(comp.name);
                          setCurrency(comp.currency);
                          setFiscalYearStart(comp.fiscal_year_start);
                          setLegalName(comp.legal_name ?? comp.name);
                          setBusinessType(comp.business_type ?? '');
                          setGstNumber(comp.gst_number ?? '');
                          setPanNumber(comp.pan_number ?? '');
                          setRegisteredAddress(comp.registered_address ?? '');
                          setLogoObjectKey(comp.logo_object_key ?? '');
                          setError(null);
                        }}
                        className="p-1.5 text-slate-500 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-indigo-500/10 rounded-lg transition-colors inline-flex items-center space-x-1"
                      >
                        <Edit2 className="h-4 w-4" />
                        <span>Edit</span>
                      </button>
                      <button
                        onClick={() => void handleToggleActive(comp)}
                        disabled={loading}
                        className={`ml-2 p-1.5 rounded-lg transition-colors inline-flex items-center space-x-1 ${comp.is_active === false ? 'text-emerald-600 hover:bg-emerald-500/10' : 'text-amber-600 hover:bg-amber-500/10'}`}
                      >
                        <Power className="h-4 w-4" />
                        <span>{comp.is_active === false ? 'Reactivate' : 'Deactivate'}</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Company Modal */}
      {isAddOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl">
            <div className="flex justify-between items-center px-6 py-4 border-b border-slate-200 dark:border-slate-800">
              <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">Add New Company</h3>
              <button onClick={() => setIsAddOpen(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleAdd} className="p-6 space-y-4">
              {error && (
                <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 text-sm flex items-start space-x-2">
                  <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Company Code
                </label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="e.g. Acme-Corp"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                  disabled={loading}
                />
                <p className="text-2xs text-slate-400">Alphanumeric and hyphens only. Permanent ID, cannot be changed later.</p>
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Company Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Acme Corporation"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                  disabled={loading}
                />
              </div>

              {extendedFields}

              {siteFields}

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Currency
                  </label>
                  <select
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                    disabled={loading}
                  >
                    <option value="INR">INR (₹)</option>
                    <option value="USD">USD ($)</option>
                    <option value="EUR">EUR (€)</option>
                    <option value="GBP">GBP (£)</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Fiscal Start (MM-DD)
                  </label>
                  <input
                    type="text"
                    value={fiscalYearStart}
                    onChange={(e) => setFiscalYearStart(e.target.value)}
                    placeholder="MM-DD (e.g. 04-01)"
                    maxLength={5}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 font-mono focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                    disabled={loading}
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAddOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 text-sm font-medium"
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-550 text-white text-sm font-medium shadow-lg shadow-indigo-500/10"
                  disabled={loading}
                >
                  {loading ? 'Creating...' : 'Create Company'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Company Modal */}
      {editingCompany && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl">
            <div className="flex justify-between items-center px-6 py-4 border-b border-slate-200 dark:border-slate-800">
              <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">Edit Company: {editingCompany.code}</h3>
              <button onClick={() => setEditingCompany(null)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleEdit} className="p-6 space-y-4">
              {error && (
                <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 text-sm flex items-start space-x-2">
                  <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Company Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Acme Corporation"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                  disabled={loading}
                />
              </div>

              {extendedFields}

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Currency
                  </label>
                  <select
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                    disabled={loading}
                  >
                    <option value="INR">INR (₹)</option>
                    <option value="USD">USD ($)</option>
                    <option value="EUR">EUR (€)</option>
                    <option value="GBP">GBP (£)</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Fiscal Start (MM-DD)
                  </label>
                  <input
                    type="text"
                    value={fiscalYearStart}
                    onChange={(e) => setFiscalYearStart(e.target.value)}
                    placeholder="MM-DD (e.g. 04-01)"
                    maxLength={5}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 font-mono focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                    disabled={loading}
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setEditingCompany(null)}
                  className="px-4 py-2 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 text-sm font-medium"
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-550 text-white text-sm font-medium shadow-lg shadow-indigo-500/10"
                  disabled={loading}
                >
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
