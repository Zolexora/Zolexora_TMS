import { useState } from 'react';
import { ComplianceDashboard } from '@/features/compliance/ComplianceDashboard';
import { ComplianceRuleManager } from '@/features/compliance/ComplianceRuleManager';

export default function CompliancePage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'rules'>('overview');

  return (
    <div className="flex-1 space-y-6">
      <div className="flex flex-col space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Compliance & Validation</h2>
        <p className="text-zinc-400">
          Monitor statutory, contractual, and internal compliance metrics across your fleet and drivers.
        </p>
      </div>

      <div className="border-b border-zinc-800">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium ${
              activeTab === 'overview'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-zinc-400 hover:border-zinc-700 hover:text-zinc-300'
            }`}
          >
            Compliance Overview
          </button>
          <button
            onClick={() => setActiveTab('rules')}
            className={`whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium ${
              activeTab === 'rules'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-zinc-400 hover:border-zinc-700 hover:text-zinc-300'
            }`}
          >
            Rule Configuration
          </button>
        </nav>
      </div>

      <div className="pt-2">
        {activeTab === 'overview' ? <ComplianceDashboard /> : <ComplianceRuleManager />}
      </div>
    </div>
  );
}
