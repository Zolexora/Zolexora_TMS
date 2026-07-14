import React from 'react';
import { AlertOctagon, RotateCw } from 'lucide-react';
import { Button } from './Button';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'System Error Encountered',
  message,
  onRetry
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center bg-red-50 dark:bg-red-950/10 border border-red-200/50 dark:border-red-900/20 rounded-2xl">
      <div className="p-4 bg-red-100 dark:bg-red-950/30 rounded-2xl text-red-600 dark:text-red-400 mb-4">
        <AlertOctagon className="h-8 w-8" />
      </div>
      <h3 className="text-lg font-bold text-red-800 dark:text-red-200">
        {title}
      </h3>
      <p className="text-sm text-red-600/80 dark:text-red-400/80 mt-1.5 max-w-md">
        {message}
      </p>
      {onRetry && (
        <Button
          onClick={onRetry}
          variant="secondary"
          className="mt-6 border border-red-200 hover:bg-red-500/10 text-red-700 dark:text-red-400 dark:border-red-900/40"
          size="sm"
          leftIcon={<RotateCw className="h-4 w-4" />}
        >
          Retry request
        </Button>
      )}
    </div>
  );
};
