import { useState } from 'react';
import { useComplianceRequirements, useCreateComplianceRequirement } from './hooks';
import { Shield, Plus, Building2, Truck, Users, XCircle, Filter } from 'lucide-react';
import type { ComplianceRequirement, ComplianceEntityType, ComplianceCategory } from './api';

export function ComplianceRuleManager() {
  const { data: requirements = [], isLoading } = useComplianceRequirements();
  const createRequirement = useCreateComplianceRequirement();
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formError, setFormError] = useState('');
  
  // Advanced Conditions State
  const [showConditions, setShowConditions] = useState(false);
  const [conditions, setConditions] = useState<Record<string, string>>({});
  const [newConditionKey, setNewConditionKey] = useState('state');
  const [newConditionValue, setNewConditionValue] = useState('');

  const [formData, setFormData] = useState<Partial<ComplianceRequirement>>({
    name: '',
    code: '',
    category: 'STATUTORY',
    entity_type: 'DRIVER',
    mandatory: true,
    blocking: true,
    verification_required: true,
    active: true,
  });

  const handleAddCondition = () => {
    if (newConditionKey && newConditionValue) {
      setConditions(prev => ({ ...prev, [newConditionKey]: newConditionValue }));
      setNewConditionValue('');
    }
  };

  const handleRemoveCondition = (key: string) => {
    const newConds = { ...conditions };
    delete newConds[key];
    setConditions(newConds);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    try {
      const payload = { ...formData, conditions: Object.keys(conditions).length > 0 ? conditions : undefined };
      await createRequirement.mutateAsync(payload);
      
      setIsModalOpen(false);
      setFormData({
        name: '',
        code: '',
        category: 'STATUTORY',
        entity_type: 'DRIVER',
        mandatory: true,
        blocking: true,
        verification_required: true,
        active: true,
      });
      setConditions({});
      setShowConditions(false);
    } catch (err: any) {
      setFormError(err.message || 'Failed to save rule. You may not have the required permissions.');
    }
  };

  const getEntityIcon = (type: string) => {
    switch (type) {
      case 'VEHICLE': return <Truck className="h-4 w-4" />;
      case 'DRIVER': return <Users className="h-4 w-4" />;
      case 'VENDOR': return <Building2 className="h-4 w-4" />;
      case 'CUSTOMER': return <Building2 className="h-4 w-4" />;
      default: return <Shield className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold">Rule Configuration</h2>
          <p className="text-sm text-zinc-500">Define compliance requirements and conditional logic.</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 transition"
        >
          <Plus className="h-4 w-4" />
          Add Rule
        </button>
      </div>

      <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-zinc-500">Loading rules...</div>
        ) : requirements.length === 0 ? (
          <div className="p-8 text-center text-zinc-500">
            No compliance rules configured. Click "Add Rule" to get started.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-zinc-50 dark:bg-zinc-800/50 text-zinc-500 uppercase text-xs">
                <tr>
                  <th className="px-6 py-4 font-medium">Entity</th>
                  <th className="px-6 py-4 font-medium">Rule Name</th>
                  <th className="px-6 py-4 font-medium">Category</th>
                  <th className="px-6 py-4 font-medium">Conditions</th>
                  <th className="px-6 py-4 font-medium">Enforcement</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {requirements.map((req) => (
                  <tr key={req.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/30">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2 text-zinc-700 dark:text-zinc-300 font-medium">
                        {getEntityIcon(req.entity_type)}
                        {req.entity_type}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-zinc-900 dark:text-zinc-100">{req.name}</div>
                      <div className="text-xs text-zinc-500 font-mono">{req.code}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center rounded-full bg-zinc-100 dark:bg-zinc-800 px-2.5 py-0.5 text-xs font-medium text-zinc-800 dark:text-zinc-300">
                        {req.category}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {req.conditions && Object.keys(req.conditions).length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {Object.entries(req.conditions).map(([k, v]) => (
                            <span key={k} className="inline-flex items-center rounded bg-indigo-500/10 px-2 py-0.5 text-[10px] font-medium text-indigo-500 border border-indigo-500/20">
                              {k}: {v as string}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-xs text-zinc-500">Universal (All)</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-1 text-xs">
                        {req.blocking ? (
                          <span className="flex items-center gap-1 text-red-500 font-medium"><XCircle className="h-3.5 w-3.5" /> BLOCKS DISPATCH</span>
                        ) : (
                          <span className="flex items-center gap-1 text-amber-500 font-medium"><Shield className="h-3.5 w-3.5" /> WARNING ONLY</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-xl rounded-2xl border border-zinc-800 bg-zinc-950 shadow-xl flex flex-col max-h-[90vh]">
            <div className="p-6 border-b border-zinc-800 flex justify-between items-center flex-shrink-0">
              <h2 className="text-xl font-bold text-white">Create Compliance Rule</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-zinc-500 hover:text-white">
                <XCircle className="h-5 w-5" />
              </button>
            </div>
            
            <div className="overflow-y-auto p-6 space-y-6">
              {formError && (
                <div className="rounded-lg bg-red-500/10 p-3 text-sm text-red-500 border border-red-500/20">
                  {formError}
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-zinc-400 mb-1">Rule Name</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                    placeholder="e.g. Commercial Driving Licence"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-1">Short Code</label>
                  <input
                    type="text"
                    required
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase().replace(/\s+/g, '_') })}
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-white font-mono uppercase focus:border-indigo-500 focus:outline-none"
                    placeholder="e.g. DL_COMMERCIAL"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-400 mb-1">Applies To Entity</label>
                  <select
                    value={formData.entity_type}
                    onChange={(e) => setFormData({ ...formData, entity_type: e.target.value as ComplianceEntityType })}
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="DRIVER">Driver</option>
                    <option value="VEHICLE">Vehicle</option>
                    <option value="VENDOR">Vendor</option>
                    <option value="CUSTOMER">Customer</option>
                  </select>
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-zinc-400 mb-1">Category</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value as ComplianceCategory })}
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="STATUTORY">Statutory (Legal/RTO)</option>
                    <option value="CONTRACTUAL">Contractual (Client Specific)</option>
                    <option value="SAFETY">Safety Policy</option>
                    <option value="INTERNAL">Internal Zolexora Policy</option>
                  </select>
                </div>
              </div>

              {/* ADVANCED CONDITIONS SECTION */}
              <div className="border border-zinc-800 rounded-xl overflow-hidden">
                <div 
                  className="bg-zinc-900 px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-zinc-800/50 transition"
                  onClick={() => setShowConditions(!showConditions)}
                >
                  <div className="flex items-center gap-2">
                    <Filter className="h-4 w-4 text-indigo-400" />
                    <span className="text-sm font-medium text-white">Advanced Conditions</span>
                    {Object.keys(conditions).length > 0 && (
                      <span className="rounded-full bg-indigo-500 px-2 py-0.5 text-xs font-bold text-white">
                        {Object.keys(conditions).length}
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-zinc-500">
                    {showConditions ? 'Hide' : 'Configure applicability'}
                  </span>
                </div>
                
                {showConditions && (
                  <div className="p-4 space-y-4 bg-zinc-950/50">
                    <p className="text-xs text-zinc-400">
                      If no conditions are added, this rule applies universally to ALL entities of the selected type.
                      Add conditions to restrict applicability (e.g., only for UP state, or ATTACHED vehicles).
                    </p>
                    
                    {Object.keys(conditions).length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(conditions).map(([k, v]) => (
                          <div key={k} className="inline-flex items-center gap-2 rounded-lg bg-zinc-900 border border-zinc-700 px-3 py-1.5 text-sm">
                            <span className="text-zinc-500">{k}:</span>
                            <span className="font-medium text-zinc-200">{v}</span>
                            <button type="button" onClick={() => handleRemoveCondition(k)} className="ml-1 text-zinc-500 hover:text-red-400">
                              <XCircle className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="flex gap-2 items-end pt-2">
                      <div className="flex-1">
                        <label className="block text-xs font-medium text-zinc-500 mb-1">Dimension</label>
                        <select
                          value={newConditionKey}
                          onChange={(e) => setNewConditionKey(e.target.value)}
                          className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                        >
                          <option value="state">State (e.g. UP, MH)</option>
                          <option value="service_type">Service Type (e.g. ETS, SPOT)</option>
                          <option value="ownership_type">Ownership (e.g. OWNED, ATTACHED)</option>
                          <option value="vehicle_category">Vehicle Category</option>
                        </select>
                      </div>
                      <div className="flex-1">
                        <label className="block text-xs font-medium text-zinc-500 mb-1">Value</label>
                        <input
                          type="text"
                          value={newConditionValue}
                          onChange={(e) => setNewConditionValue(e.target.value.toUpperCase())}
                          placeholder="e.g. UP or ETS"
                          className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleAddCondition(); } }}
                        />
                      </div>
                      <button
                        type="button"
                        onClick={handleAddCondition}
                        disabled={!newConditionValue}
                        className="rounded-lg bg-zinc-800 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50 transition"
                      >
                        Add
                      </button>
                    </div>
                  </div>
                )}
              </div>

              <div className="pt-2 border-t border-zinc-800 space-y-3">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.blocking}
                    onChange={(e) => setFormData({ ...formData, blocking: e.target.checked })}
                    className="h-4 w-4 rounded border-zinc-700 bg-zinc-900 text-indigo-600 focus:ring-indigo-600 focus:ring-offset-zinc-900 cursor-pointer"
                  />
                  <div>
                    <p className="text-sm font-medium text-white">Blocking Rule</p>
                    <p className="text-xs text-zinc-500">If missing or expired, this entity CANNOT be dispatched.</p>
                  </div>
                </label>
                
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.verification_required}
                    onChange={(e) => setFormData({ ...formData, verification_required: e.target.checked })}
                    className="h-4 w-4 rounded border-zinc-700 bg-zinc-900 text-indigo-600 focus:ring-indigo-600 focus:ring-offset-zinc-900 cursor-pointer"
                  />
                  <div>
                    <p className="text-sm font-medium text-white">Requires Manual Verification</p>
                    <p className="text-xs text-zinc-500">Uploads must be approved by a compliance officer before becoming VALID.</p>
                  </div>
                </label>
              </div>
            </div>

            <div className="p-6 border-t border-zinc-800 flex justify-end gap-3 flex-shrink-0 bg-zinc-950">
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="rounded-lg px-4 py-2 text-sm font-medium text-zinc-400 hover:text-white transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={createRequirement.isPending}
                className="rounded-lg bg-indigo-600 px-6 py-2 text-sm font-semibold text-white hover:bg-indigo-500 transition disabled:opacity-50"
              >
                {createRequirement.isPending ? 'Saving...' : 'Save Rule'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
