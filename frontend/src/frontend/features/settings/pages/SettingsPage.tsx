import React, { useState } from 'react';
import { 
  Settings, Save, CheckCircle, Database, Lock 
} from 'lucide-react';
import { Button } from '../../../components/Button';
import { Select } from '../../../components/Select';

export const SettingsPage: React.FC = () => {
  const [sessionDuration, setSessionDuration] = useState('3600');
  const [auditRetention, setAuditRetention] = useState('90');
  const [successMsg, setSuccessMsg] = useState(false);

  const durationOptions = [
    { value: '1800', label: '30 Minutes' },
    { value: '3600', label: '1 Hour' },
    { value: '7200', label: '2 Hours' },
    { value: '86400', label: '24 Hours' }
  ];

  const retentionOptions = [
    { value: '30', label: '30 Days' },
    { value: '90', label: '90 Days' },
    { value: '365', label: '365 Days' },
    { value: '0', label: 'Keep Indefinitely' }
  ];

  const handleSave = () => {
    setSuccessMsg(true);
    setTimeout(() => {
      setSuccessMsg(false);
    }, 3000);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header Panel */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-slate-100 flex items-center space-x-2">
            <Settings className="h-7 w-7 text-indigo-500" />
            <span>General Settings</span>
          </h2>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Configure system parameters, audit policies, and security settings.
          </p>
        </div>
        <Button variant="primary" leftIcon={<Save className="h-4 w-4" />} onClick={handleSave}>
          Save Settings
        </Button>
      </div>

      {/* Success Notification */}
      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-sm flex items-center space-x-2 animate-fadeIn">
          <CheckCircle className="h-5 w-5 flex-shrink-0" />
          <span>System preferences updated successfully! Changes applied to Cloudflare runtime settings.</span>
        </div>
      )}

      {/* Settings Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Security & Access Panel */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900/60 border border-slate-200/50 dark:border-slate-850 shadow-sm space-y-5">
          <div className="flex items-center space-x-2 pb-3 border-b border-slate-100 dark:border-slate-800">
            <Lock className="h-5 w-5 text-indigo-500" />
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider">Security & Access</h3>
          </div>
          <Select 
            label="Inactivity Session Duration"
            options={durationOptions}
            value={sessionDuration}
            onChange={(e) => setSessionDuration(e.target.value)}
            helperText="Maximum allowed inactive duration before session key is invalidated."
          />
          <div className="space-y-1.5">
            <label className="block text-sm font-semibold text-slate-700 dark:text-slate-350">Cloudflare Access Integration</label>
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 flex items-center justify-between">
              <div className="space-y-0.5">
                <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">Identity Protection</span>
                <p className="text-[10px] text-slate-400">Offload OAuth verification to Cloudflare Edge gateway.</p>
              </div>
              <span className="inline-flex px-2 py-0.5 rounded-full text-3xs font-extrabold bg-indigo-500/10 text-indigo-500 border border-indigo-500/20">Active</span>
            </div>
          </div>
        </div>

        {/* Database & Audit Policies */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900/60 border border-slate-200/50 dark:border-slate-850 shadow-sm space-y-5">
          <div className="flex items-center space-x-2 pb-3 border-b border-slate-100 dark:border-slate-800">
            <Database className="h-5 w-5 text-indigo-500" />
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider">Database & Auditing</h3>
          </div>
          <Select 
            label="Audit Trail Retention Limit"
            options={retentionOptions}
            value={auditRetention}
            onChange={(e) => setAuditRetention(e.target.value)}
            helperText="Duration after which temporary background audits are deleted."
          />
          <div className="space-y-1.5">
            <label className="block text-sm font-semibold text-slate-700 dark:text-slate-350">D1 Schema Version</label>
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 flex justify-between items-center font-mono text-2xs text-slate-500">
              <span>Migration Level:</span>
              <span className="font-bold text-indigo-500">0002_core_foundation.sql</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
