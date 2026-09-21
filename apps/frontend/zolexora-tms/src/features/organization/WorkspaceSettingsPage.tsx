import { useState } from 'react';
import { useAuth } from '../auth/useAuth';
import { ShieldAlert, AlertTriangle } from 'lucide-react';
import { apiClient } from '../../lib/api';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';

export function WorkspaceSettingsPage() {
  const { isCommander, organisation } = useAuth();
  const [transferTarget, setTransferTarget] = useState('');
  const [showTransfer, setShowTransfer] = useState(false);
  
  const transferMutation = useMutation({
    mutationFn: async (targetId: string) => {
      return apiClient('/api/v1/organisations/commander/transfer', {
        method: 'POST',
        body: JSON.stringify({
          new_commander_user_id: targetId,
          former_commander_role: 'ADMIN'
        })
      });
    },
    onSuccess: () => {
      toast.success('Commander authority transferred successfully');
      window.location.reload();
    },
    onError: (err: any) => {
      toast.error(err.message || 'Failed to transfer commander authority');
    }
  });

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-white mb-6">Workspace & Security Settings</h1>
      
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 mb-8">
        <h2 className="text-xl font-semibold text-white mb-4">Organisation Profile</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-slate-400">Name</p>
            <p className="text-lg text-slate-200">{organisation?.name}</p>
          </div>
          <div>
            <p className="text-sm text-slate-400">Type</p>
            <p className="text-lg text-slate-200">{organisation?.organisation_type}</p>
          </div>
        </div>
      </div>

      {isCommander && (
        <div className="bg-red-950/20 border border-red-900/50 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <ShieldAlert className="h-6 w-6 text-red-500" />
            <h2 className="text-xl font-semibold text-white">Commander Settings</h2>
          </div>
          <p className="text-slate-400 mb-6">
            You are the current Commander of this organisation. You have unrestricted access to all active modules.
          </p>
          
          {!showTransfer ? (
            <button 
              onClick={() => setShowTransfer(true)}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition"
            >
              Transfer Commander Authority
            </button>
          ) : (
            <div className="bg-slate-900 border border-red-900/50 rounded-lg p-4">
              <div className="flex items-start gap-3 mb-4 text-red-400 bg-red-950/30 p-3 rounded border border-red-900/30">
                <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
                <p className="text-sm">
                  Warning: Transferring Commander authority immediately removes Commander authority from you. This action cannot be undone.
                </p>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">New Commander (User ID)</label>
                  <input 
                    type="text" 
                    value={transferTarget}
                    onChange={(e) => setTransferTarget(e.target.value)}
                    placeholder="Enter User ID of active member"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white"
                  />
                </div>
                
                <div className="flex gap-3 pt-2">
                  <button 
                    onClick={() => transferMutation.mutate(transferTarget)}
                    disabled={!transferTarget || transferMutation.isPending}
                    className="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-medium transition"
                  >
                    {transferMutation.isPending ? 'Transferring...' : 'Confirm Transfer'}
                  </button>
                  <button 
                    onClick={() => setShowTransfer(false)}
                    className="bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
