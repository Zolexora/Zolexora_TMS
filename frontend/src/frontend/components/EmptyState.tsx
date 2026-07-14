import React from 'react';
import { Database } from 'lucide-react';
import { Button } from './Button';

interface EmptyStateProps {
  title?: string;
  description: string;
  icon?: React.ReactNode;
  actionText?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Records Found',
  description,
  icon,
  actionText,
  onAction
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center bg-white dark:bg-slate-900/40 border border-slate-200/60 dark:border-slate-850 rounded-2xl shadow-sm">
      <div className="p-4 bg-indigo-50 dark:bg-indigo-950/30 rounded-2xl text-indigo-600 dark:text-indigo-400 mb-4 animate-pulse">
        {icon || <Database className="h-8 w-8" />}
      </div>
      <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">
        {title}
      </h3>
      <p className="text-sm text-slate-500 dark:text-slate-400 mt-1.5 max-w-sm">
        {description}
      </p>
      {actionText && onAction && (
        <Button
          onClick={onAction}
          className="mt-6 shadow-indigo-500/10"
          size="sm"
        >
          {actionText}
        </Button>
      )}
    </div>
  );
};
