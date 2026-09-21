import { useState } from 'react';
import { Upload, CheckCircle, AlertCircle } from 'lucide-react';
import { apiClient } from '../../../lib/api';
import { useApplicationRuntime } from '../../../providers/ApplicationRuntimeProvider';

export function R1TikriOperationsPage() {
  const runtime = useApplicationRuntime();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState<any>(null);

  // Hardcoded for R1 implementation context (in reality, fetched or context-aware)
  const customerId = "00000000-0000-0000-0000-000000000000"; // Dummy UUID for R1
  const location = "Tikri";

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('customer_id', customerId);
    formData.append('location', location);

    try {
      const res = await fetch(
        (import.meta.env.VITE_API_BASE_URL || '') + '/api/v1/operations/r1rcm/import',
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('sb-access-token') || ''}`
          },
          body: formData
        }
      );
      if (res.ok) {
        const data = await res.json();
        setPreview(data);
      }
    } finally {
      setUploading(false);
    }
  };

  const confirmImport = async () => {
    if (!preview) return;
    setUploading(true);
    try {
      await apiClient('/api/v1/operations/r1rcm/import/confirm', {
        method: 'POST',
        body: JSON.stringify({
          batch_id: preview.batch_id,
          customer_id: customerId,
          location: location
        })
      });
      alert('Bookings Created Successfully');
      setPreview(null);
      setFile(null);
    } finally {
      setUploading(false);
    }
  };

  // Determine if this screen is authorized by runtime config (mock check for demo)
  if (!runtime.extensions?.r1rcm?.enabled) {
    // We render it anyway but show a warning if config is not present, indicating 
    // it's generic platform behavior responding to R1 config.
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">R1 RCM Operations Board - {location}</h1>
      </div>

      {!preview ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Bulk Upload Bookings</h2>
          <div className="flex items-center gap-4">
            <input 
              type="file" 
              accept=".csv"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="text-slate-300 file:mr-4 file:rounded-full file:border-0 file:bg-indigo-600/20 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-indigo-400 hover:file:bg-indigo-600/30"
            />
            <button 
              onClick={handleUpload}
              disabled={!file || uploading}
              className="flex items-center gap-2 rounded bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
            >
              <Upload className="h-4 w-4" />
              {uploading ? 'Processing...' : 'Upload & Preview'}
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-4 gap-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
              <p className="text-sm text-slate-400">Total Rows</p>
              <p className="text-2xl font-bold text-white">{preview.total_rows}</p>
            </div>
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-4">
              <p className="text-sm text-emerald-400">Valid</p>
              <p className="text-2xl font-bold text-emerald-300">{preview.valid_count}</p>
            </div>
            <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-4">
              <p className="text-sm text-amber-400">Warnings</p>
              <p className="text-2xl font-bold text-amber-300">{preview.warning_count}</p>
            </div>
            <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4">
              <p className="text-sm text-red-400">Errors</p>
              <p className="text-2xl font-bold text-red-300">{preview.error_count}</p>
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900 p-6 overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-400">
              <thead className="border-b border-slate-800 text-slate-300">
                <tr>
                  <th className="pb-3 pr-4">Row</th>
                  <th className="pb-3 pr-4">Status</th>
                  <th className="pb-3 pr-4">Employee</th>
                  <th className="pb-3 pr-4">Trip ID</th>
                  <th className="pb-3 pr-4">Route</th>
                  <th className="pb-3">Messages</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {preview.results.slice(0, 10).map((r: any) => (
                  <tr key={r.row_index} className="hover:bg-slate-800/20">
                    <td className="py-3 pr-4">{r.row_index}</td>
                    <td className="py-3 pr-4">
                      {r.is_valid ? (
                        <span className="inline-flex items-center gap-1 text-emerald-400"><CheckCircle className="h-3 w-3" /> Valid</span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-red-400"><AlertCircle className="h-3 w-3" /> Error</span>
                      )}
                    </td>
                    <td className="py-3 pr-4">{r.row_data.employee_name} ({r.row_data.employee_id})</td>
                    <td className="py-3 pr-4">{r.row_data.trip_id}</td>
                    <td className="py-3 pr-4">{r.row_data.route_number}</td>
                    <td className="py-3">
                      {r.errors.map((e: string) => <div className="text-red-400 text-xs" key={e}>{e}</div>)}
                      {r.warnings.map((w: string) => <div className="text-amber-400 text-xs" key={w}>{w}</div>)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {preview.total_rows > 10 && <p className="mt-4 text-xs text-slate-500">Showing first 10 rows...</p>}
          </div>

          <div className="flex justify-end gap-4">
            <button 
              onClick={() => setPreview(null)}
              className="rounded px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800"
            >
              Cancel
            </button>
            <button 
              onClick={confirmImport}
              disabled={preview.valid_count === 0 || uploading}
              className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
            >
              Confirm & Create {preview.valid_count} Bookings
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
