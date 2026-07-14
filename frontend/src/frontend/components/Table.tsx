import React from 'react';

interface Column<T> {
  key: string;
  header: string;
  align?: 'left' | 'center' | 'right';
  render?: (item: T, index: number) => React.ReactNode;
  className?: string;
}

interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (item: T, index: number) => string | number;
  emptyMessage?: string;
  onRowClick?: (item: T) => void;
  isLoading?: boolean;
}

export function Table<T>({
  columns,
  data,
  keyExtractor,
  emptyMessage = 'No records available.',
  onRowClick,
  isLoading = false
}: TableProps<T>) {
  return (
    <div className="w-full overflow-x-auto rounded-2xl border border-slate-200/60 dark:border-slate-850 shadow-sm bg-white dark:bg-slate-900/40">
      <table className="min-w-full divide-y divide-slate-200/60 dark:divide-slate-850 text-left border-collapse">
        <thead className="bg-slate-50 dark:bg-slate-900/80 sticky top-0">
          <tr>
            {columns.map((col) => {
              const alignClass = 
                col.align === 'right' ? 'text-right' : 
                col.align === 'center' ? 'text-center' : 'text-left';
              return (
                <th
                  key={col.key}
                  scope="col"
                  className={`px-6 py-4 text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500 font-mono ${alignClass} ${col.className || ''}`}
                >
                  {col.header}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800 bg-transparent">
          {isLoading ? (
            <tr>
              <td colSpan={columns.length} className="px-6 py-12 text-center">
                <div className="flex justify-center items-center space-x-2">
                  <div className="h-5 w-5 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
                  <span className="text-sm text-slate-400 font-medium">Fetching table records...</span>
                </div>
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-6 py-12 text-center text-sm text-slate-400 dark:text-slate-500 font-medium">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((item, idx) => (
              <tr
                key={keyExtractor(item, idx)}
                onClick={() => onRowClick && onRowClick(item)}
                className={`transition-colors duration-150 ${
                  onRowClick 
                    ? 'cursor-pointer hover:bg-slate-50/50 dark:hover:bg-slate-850/50' 
                    : 'hover:bg-slate-50/30 dark:hover:bg-slate-900/10'
                }`}
              >
                {columns.map((col) => {
                  const alignClass = 
                    col.align === 'right' ? 'text-right' : 
                    col.align === 'center' ? 'text-center' : 'text-left';
                  return (
                    <td
                      key={col.key}
                      className={`px-6 py-4 text-sm text-slate-700 dark:text-slate-300 whitespace-nowrap ${alignClass} ${col.className || ''}`}
                    >
                      {col.render ? col.render(item, idx) : (item as any)[col.key]}
                    </td>
                  );
                })}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
