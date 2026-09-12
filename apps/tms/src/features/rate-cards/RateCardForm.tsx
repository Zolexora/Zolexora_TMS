import { useState } from 'react';
import { useCreateRateCard } from './hooks';
import { X, Plus, Trash2, CheckCircle2 } from 'lucide-react';

interface RateCardFormProps {
  onClose: () => void;
}

export function RateCardForm({ onClose }: RateCardFormProps) {
  const createMutation = useCreateRateCard();
  const [formError, setFormError] = useState('');
  
  const [name, setName] = useState('');
  const [side, setSide] = useState<'CUSTOMER'|'VENDOR'>('CUSTOMER');
  const [serviceType,  ] = useState('ETS');
  
  const [rules, setRules] = useState<any[]>([
    {
      rule_type: 'FIXED_TRIP',
      name: 'Base Duty Rate',
      base_amount: 0,
      quantity_included: 1,
      rate_per_unit: 0,
      is_percentage: false,
      percentage_value: 0,
      sequence: 10
    }
  ]);

  const addRule = () => {
    setRules([...rules, {
      rule_type: 'EXTRA_KM',
      name: 'Extra KM Charge',
      base_amount: 0,
      quantity_included: 0,
      rate_per_unit: 0,
      is_percentage: false,
      percentage_value: 0,
      sequence: rules.length * 10 + 10
    }]);
  };

  const updateRule = (index: number, field: string, value: any) => {
    const newRules = [...rules];
    newRules[index][field] = value;
    setRules(newRules);
  };

  const removeRule = (index: number) => {
    setRules(rules.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    try {
      await createMutation.mutateAsync({
        name,
        side,
        service_type: serviceType,
        active: true,
        initial_version: {
          version_number: 1,
          effective_from: new Date().toISOString(),
          is_immutable: true,
          rules
        }
      });
      onClose();
    } catch (err: any) {
      setFormError(err.message || 'Failed to create rate card');
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="w-full max-w-4xl rounded-2xl border border-slate-800 bg-slate-950 shadow-2xl flex flex-col my-8">
        <div className="p-6 border-b border-slate-800 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-white">Create Deterministic Rate Card</h2>
            <p className="text-sm text-slate-400">Define financial rules for {side.toLowerCase()} side pricing.</p>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          {formError && (
            <div className="rounded-lg bg-red-500/10 p-3 text-sm text-red-500 border border-red-500/20">
              {formError}
            </div>
          )}
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Rate Card Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
                placeholder="e.g. ABC Ltd - ETS Sedan 2026"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Pricing Side</label>
              <select
                value={side}
                onChange={(e) => setSide(e.target.value as 'CUSTOMER'|'VENDOR')}
                className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-white focus:border-indigo-500 focus:outline-none"
              >
                <option value="CUSTOMER">CUSTOMER (Revenue)</option>
                <option value="VENDOR">VENDOR (Cost / Payable)</option>
              </select>
            </div>
          </div>

          <div className="border-t border-slate-800 pt-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Rate Components</h3>
              <button 
                type="button" 
                onClick={addRule}
                className="inline-flex items-center gap-1 rounded-lg bg-slate-800 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700"
              >
                <Plus className="h-4 w-4" /> Add Component
              </button>
            </div>
            
            <div className="space-y-4">
              {rules.map((rule, idx) => (
                <div key={idx} className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
                  <div className="flex justify-between items-start mb-3">
                    <input 
                      type="text" 
                      value={rule.name}
                      onChange={(e) => updateRule(idx, 'name', e.target.value)}
                      className="bg-transparent text-white font-medium focus:outline-none border-b border-dashed border-slate-700 pb-1" 
                    />
                    {idx > 0 && (
                      <button type="button" onClick={() => removeRule(idx)} className="text-slate-500 hover:text-red-400">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                  
                  <div className="grid grid-cols-4 gap-4">
                    <div>
                      <label className="block text-xs text-slate-500 mb-1">Rule Type</label>
                      <select 
                        value={rule.rule_type}
                        onChange={(e) => updateRule(idx, 'rule_type', e.target.value)}
                        className="w-full rounded-lg border border-slate-800 bg-slate-950 px-2 py-1.5 text-sm text-slate-300"
                      >
                        <option value="FIXED_TRIP">Fixed / Base Trip</option>
                        <option value="PER_KM">Per KM (Flat)</option>
                        <option value="EXTRA_KM">Extra KM (Beyond limit)</option>
                        <option value="PER_HOUR">Per Hour</option>
                        <option value="EXTRA_HOUR">Extra Hour</option>
                        <option value="WAITING_CHARGE">Waiting Charge</option>
                        <option value="NIGHT_SURCHARGE">Night Surcharge</option>
                        <option value="TOLL">Toll (Pass-through)</option>
                        <option value="TAX_CGST">CGST Tax (%)</option>
                        <option value="TAX_SGST">SGST Tax (%)</option>
                      </select>
                    </div>
                    
                    {rule.rule_type.startsWith('TAX') ? (
                       <div>
                         <label className="block text-xs text-slate-500 mb-1">Percentage (%)</label>
                         <input 
                           type="number" 
                           value={rule.percentage_value}
                           onChange={(e) => {
                             updateRule(idx, 'percentage_value', parseFloat(e.target.value));
                             updateRule(idx, 'is_percentage', true);
                           }}
                           className="w-full rounded-lg border border-slate-800 bg-slate-950 px-2 py-1.5 text-sm text-slate-300"
                         />
                       </div>
                    ) : (
                      <>
                        <div>
                          <label className="block text-xs text-slate-500 mb-1">Base/Fixed Amt (₹)</label>
                          <input 
                            type="number" 
                            value={rule.base_amount}
                            onChange={(e) => updateRule(idx, 'base_amount', parseFloat(e.target.value))}
                            className="w-full rounded-lg border border-slate-800 bg-slate-950 px-2 py-1.5 text-sm text-slate-300"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-slate-500 mb-1">Qty Included</label>
                          <input 
                            type="number" 
                            value={rule.quantity_included}
                            onChange={(e) => updateRule(idx, 'quantity_included', parseFloat(e.target.value))}
                            className="w-full rounded-lg border border-slate-800 bg-slate-950 px-2 py-1.5 text-sm text-slate-300"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-slate-500 mb-1">Rate Per Unit (₹)</label>
                          <input 
                            type="number" 
                            value={rule.rate_per_unit}
                            onChange={(e) => updateRule(idx, 'rate_per_unit', parseFloat(e.target.value))}
                            className="w-full rounded-lg border border-slate-800 bg-slate-950 px-2 py-1.5 text-sm text-slate-300"
                          />
                        </div>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </form>

        <div className="p-6 border-t border-slate-800 bg-slate-900 flex justify-end gap-3 rounded-b-2xl">
          <button type="button" onClick={onClose} className="rounded-lg px-4 py-2 text-sm font-medium text-slate-400 hover:text-white">
            Cancel
          </button>
          <button 
            onClick={handleSubmit}
            disabled={createMutation.isPending}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-6 py-2 text-sm font-bold text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {createMutation.isPending ? 'Saving...' : (
              <><CheckCircle2 className="h-4 w-4" /> Save Rate Card</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
