import React from 'react';

interface LoadingStateProps {
  message?: string;
  variant?: 'spinner' | 'skeleton';
}

export const LoadingState: React.FC<LoadingStateProps> = ({ 
  message = 'Loading dashboard assets...', 
  variant = 'spinner' 
}) => {
  if (variant === 'skeleton') {
    return (
      <div className="w-full space-y-4 animate-pulse">
        <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded-xl w-1/4"></div>
        <div className="h-40 bg-slate-200 dark:bg-slate-800 rounded-2xl w-full"></div>
        <div className="space-y-2">
          <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded-lg w-full"></div>
          <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded-lg w-5/6"></div>
          <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded-lg w-2/3"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center py-20 px-4">
      <div className="relative flex items-center justify-center">
        <div className="h-12 w-12 border-4 border-indigo-500/20 border-t-indigo-600 rounded-full animate-spin"></div>
        <div className="absolute h-6 w-6 rounded-full bg-indigo-500/10 animate-ping"></div>
      </div>
      {message && (
        <span className="text-sm font-semibold text-slate-500 dark:text-slate-400 mt-4 tracking-wide">
          {message}
        </span>
      )}
    </div>
  );
};
