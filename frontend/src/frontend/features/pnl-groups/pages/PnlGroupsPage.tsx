import React, { useState, useEffect } from 'react';
import { api } from '../../../api/client';
import { PLGroup } from '../../../../shared/types';
import { Plus, Edit2, FolderOpen, AlertCircle, X, Power, ShieldAlert } from 'lucide-react';
import { useCompany } from '../../companies/context/CompanyContext';
import { useAuth } from '../../auth/hooks/useAuth';
import { PERMISSIONS } from '../../../../shared/permissions';

export function getForbiddenParents(groups: PLGroup[], selectedGroupId: string): Set<string> {
  const forbidden = new Set<string>([selectedGroupId]);
  const queue: string[] = [selectedGroupId];
  
  while (queue.length > 0) {
    const currentId = queue.shift()!;
    const children = groups.filter(g => g.parent_id !== null && String(g.parent_id) === currentId);
    for (const child of children) {
      const childId = String(child.id);
      if (!forbidden.has(childId)) {
        forbidden.add(childId);
        queue.push(childId);
      }
    }
  }
  return forbidden;
}

export const PnlGroupsPage: React.FC = () => {
  const { activeCompany } = useCompany();
  const { can } = useAuth();
  const [groups, setGroups] = useState<PLGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Modal states
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [editingGroup, setEditingGroup] = useState<PLGroup | null>(null);

  // Form states
  const [id, setId] = useState('');
  const [name, setName] = useState('');
  const [parentId, setParentId] = useState<string>('');
  const [displayOrder, setDisplayOrder] = useState<number>(0);
  const [normalDirection, setNormalDirection] = useState<'debit' | 'credit'>('debit');

  const fetchGroups = async () => {
    if (!activeCompany) { setGroups([]); return; }
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<PLGroup[]>(`/pl-groups?company_code=${encodeURIComponent(activeCompany.code)}`);
      setGroups(data || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load P&L Groups.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGroups();
  }, [activeCompany?.code]);

  const resetForm = () => {
    setId('');
    setName('');
    setParentId('');
    setDisplayOrder(0);
    setNormalDirection('debit');
    setError(null);
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCompany) return;
    if (!id.trim()) {
      setError('Group ID is required.');
      return;
    }
    if (!name.trim()) {
      setError('Group Name is required.');
      return;
    }

    try {
      setError(null);
      await api.post('/pl-groups', {
        id: id.trim(),
        code: id.trim(),
        company_code: activeCompany.code,
        name: name.trim(),
        parent_id: parentId ? parentId : null,
        display_order: displayOrder,
        normal_direction: normalDirection,
      });
      await fetchGroups();
      setIsAddOpen(false);
      resetForm();
    } catch (err: any) {
      setError(err.message || 'Failed to create P&L group.');
    }
  };

  const toggleActive = async (group: PLGroup) => {
    try {
      setError(null);
      await api.patch(`/pl-groups/${group.id}`, { is_active: !group.is_active });
      await fetchGroups();
    } catch (err: any) {
      setError(err.message || 'Failed to change P&L group status.');
    }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingGroup) return;
    if (!name.trim()) {
      setError('Group Name is required.');
      return;
    }

    // Double check cycle prevention in frontend before submitting
    const forbidden = getForbiddenParents(groups, String(editingGroup.id));
    if (parentId && forbidden.has(parentId)) {
      setError('Circular reference detected! You cannot select this group or any of its children as the parent.');
      return;
    }

    try {
      setError(null);
      await api.patch(`/pl-groups/${editingGroup.id}`, {
        name: name.trim(),
        parent_id: parentId ? parentId : null,
        display_order: displayOrder,
        normal_direction: normalDirection,
      });
      await fetchGroups();
      setEditingGroup(null);
      resetForm();
    } catch (err: any) {
      setError(err.message || 'Failed to update P&L group.');
    }
  };

  // Preorder traversal to generate dropdown options
  const getPreorderGroups = (groupsList: PLGroup[]): { group: PLGroup; depth: number }[] => {
    const result: { group: PLGroup; depth: number }[] = [];
    const visited = new Set<string>();

    const dfs = (pId: string | null, depth: number) => {
      const levelGroups = groupsList.filter(g => 
        pId === null 
          ? (!g.parent_id || !groupsList.some(parent => String(parent.id) === String(g.parent_id)))
          : String(g.parent_id) === pId
      );
      levelGroups.sort((a, b) => (a.display_order || 0) - (b.display_order || 0));

      for (const g of levelGroups) {
        const gId = String(g.id);
        if (visited.has(gId)) continue;
        visited.add(gId);
        result.push({ group: g, depth });
        dfs(gId, depth + 1);
      }
    };

    dfs(null, 0);
    return result;
  };

  // Render tree node recursively
  const renderTreeNode = (pId: string | null, depth: number) => {
    const nodes = groups.filter(g => 
      pId === null 
        ? (!g.parent_id || !groups.some(parent => String(parent.id) === String(g.parent_id)))
        : String(g.parent_id) === pId
    );
    nodes.sort((a, b) => (a.display_order || 0) - (b.display_order || 0));

    if (nodes.length === 0) return null;

    return (
      <div className={`space-y-2 ${depth > 0 ? 'pl-6 border-l border-slate-200 dark:border-slate-800 ml-4 mt-2' : ''}`}>
        {nodes.map(node => (
          <div key={node.id} className="group/node">
            <div className="flex items-center justify-between p-3 rounded-xl border border-slate-200/60 dark:border-slate-850 bg-slate-50/50 dark:bg-slate-900/30 hover:bg-slate-50 dark:hover:bg-slate-850/30 transition-all shadow-sm">
              <div className="flex items-center space-x-2.5">
                <FolderOpen className="h-4 w-4 text-indigo-500 flex-shrink-0" />
                <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-3">
                  <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">{node.name}</span>
                  <span className="text-2xs font-mono text-slate-400">({node.id})</span>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <span className={`px-2 py-0.5 rounded-md text-3xs font-bold uppercase tracking-wider ${
                  node.normal_direction === 'credit'
                    ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400'
                    : 'bg-indigo-100 text-indigo-800 dark:bg-indigo-950/40 dark:text-indigo-400'
                }`}>
                  {node.normal_direction === 'credit' ? 'Revenue' : 'Expense'}
                </span>
                <span className={`px-2 py-0.5 rounded-md text-3xs font-bold ${node.is_active === false ? 'bg-slate-200 text-slate-600' : 'bg-emerald-100 text-emerald-700'}`}>
                  {node.is_active === false ? 'Inactive' : node.is_system ? 'System' : 'Active'}
                </span>
                
                {node.display_order !== undefined && (
                  <span className="bg-slate-200 dark:bg-slate-800 text-slate-500 dark:text-slate-400 px-2 py-0.5 rounded-md text-3xs font-semibold">
                    Ord: {node.display_order}
                  </span>
                )}

                <button
                  onClick={() => {
                    setEditingGroup(node);
                    setId(String(node.id));
                    setName(node.name);
                    setParentId(node.parent_id ? String(node.parent_id) : '');
                    setDisplayOrder(node.display_order || 0);
                    setNormalDirection(node.normal_direction);
                    setError(null);
                  }}
                  className="p-1 text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-indigo-500/10 rounded transition-colors"
                >
                  <Edit2 className="h-3.5 w-3.5" />
                </button>
                {can(PERMISSIONS.PL_GROUP_MANAGE) && (
                  <button onClick={() => void toggleActive(node)} title={node.is_active === false ? 'Reactivate' : 'Deactivate'}
                    className="p-1 text-amber-600 hover:bg-amber-500/10 rounded transition-colors">
                    <Power className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            </div>
            {renderTreeNode(String(node.id), depth + 1)}
          </div>
        ))}
      </div>
    );
  };

  const orderedGroups = getPreorderGroups(groups);

  if (!activeCompany) return (
    <div className="flex flex-col items-center justify-center py-12 rounded-2xl border border-slate-200 dark:border-slate-800">
      <ShieldAlert className="h-12 w-12 text-amber-500 mb-4" /><h3 className="font-bold">Select a company to manage P&L groups</h3>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center space-y-4 sm:space-y-0">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-800 dark:text-slate-100">P&L Groups Tree Editor</h2>
          <p className="text-slate-500 dark:text-slate-400">
            Define hierarchical classifications for Revenues and Expenses. Prevents cycles recursively.
          </p>
        </div>
        {can(PERMISSIONS.PL_GROUP_MANAGE) && <button
          onClick={() => {
            resetForm();
            setIsAddOpen(true);
          }}
          className="flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-xl transition-all shadow-md shadow-indigo-500/10 self-start sm:self-auto font-medium"
        >
          <Plus className="h-4 w-4" />
          <span>Add Group</span>
        </button>}
      </div>

      {loading && groups.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl">
          <div className="h-8 w-8 border-4 border-indigo-500/30 border-t-indigo-600 rounded-full animate-spin mb-4"></div>
          <span className="text-sm text-slate-500">Loading hierarchy structure...</span>
        </div>
      ) : (
        <div className="p-6 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-850 backdrop-blur-md rounded-2xl shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Structure Tree</span>
            <span className="text-2xs text-slate-400">Indented lines display parent-child scopes</span>
          </div>

          {groups.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              No P&L groups configured yet. Click "Add Group" to build your hierarchy.
            </div>
          ) : (
            renderTreeNode(null, 0)
          )}
        </div>
      )}

      {/* Add Group Modal */}
      {isAddOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden">
            <div className="flex justify-between items-center px-6 py-4 border-b border-slate-200 dark:border-slate-800">
              <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">Add P&L Group</h3>
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
                  Group ID (Unique Key)
                </label>
                <input
                  type="text"
                  value={id}
                  onChange={(e) => setId(e.target.value)}
                  placeholder="e.g. sales-revenue"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Group Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Sales Revenue"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Parent Group
                </label>
                <select
                  value={parentId}
                  onChange={(e) => setParentId(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="">[None — Root Group]</option>
                  {orderedGroups.map(item => (
                    <option key={item.group.id} value={item.group.id}>
                      {'\u00A0'.repeat(item.depth * 2)}{item.depth > 0 ? '↳ ' : ''}{item.group.name} ({item.group.id})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Normal Balance
                  </label>
                  <select
                    value={normalDirection}
                    onChange={(e) => setNormalDirection(e.target.value as any)}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="debit">Debit (Expense)</option>
                    <option value="credit">Credit (Revenue)</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Display Order
                  </label>
                  <input
                    type="number"
                    value={displayOrder}
                    onChange={(e) => setDisplayOrder(Number(e.target.value))}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAddOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-550 text-white text-sm font-medium shadow-lg shadow-indigo-500/10"
                >
                  Create Group
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Group Modal */}
      {editingGroup && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden">
            <div className="flex justify-between items-center px-6 py-4 border-b border-slate-200 dark:border-slate-800">
              <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">Edit P&L Group: {editingGroup.id}</h3>
              <button onClick={() => setEditingGroup(null)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
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
                  Group Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Sales Revenue"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Parent Group
                </label>
                <select
                  value={parentId}
                  onChange={(e) => setParentId(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="">[None — Root Group]</option>
                  {orderedGroups.map(item => {
                    const isSelf = String(item.group.id) === String(editingGroup.id);
                    const forbidden = getForbiddenParents(groups, String(editingGroup.id));
                    const isForbidden = forbidden.has(String(item.group.id));

                    return (
                      <option
                        key={item.group.id}
                        value={item.group.id}
                        disabled={isForbidden}
                        className={isForbidden ? 'text-slate-400 dark:text-slate-600 bg-slate-100/50 dark:bg-slate-950/20' : ''}
                      >
                        {'\u00A0'.repeat(item.depth * 2)}
                        {item.depth > 0 ? '↳ ' : ''}
                        {item.group.name} ({item.group.id})
                        {isSelf ? ' [Current Group]' : isForbidden ? ' [Forbidden Cycle]' : ''}
                      </option>
                    );
                  })}
                </select>
                <p className="text-2xs text-slate-400">Disables cyclic descendants to preserve strict trees.</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Normal Balance
                  </label>
                  <select
                    value={normalDirection}
                    onChange={(e) => setNormalDirection(e.target.value as any)}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="debit">Debit (Expense)</option>
                    <option value="credit">Credit (Revenue)</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Display Order
                  </label>
                  <input
                    type="number"
                    value={displayOrder}
                    onChange={(e) => setDisplayOrder(Number(e.target.value))}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setEditingGroup(null)}
                  className="px-4 py-2 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-550 text-white text-sm font-medium shadow-lg shadow-indigo-500/10"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
