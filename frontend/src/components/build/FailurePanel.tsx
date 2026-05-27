import React, { useState } from 'react';
import { AlertCircle, ChevronDown, ChevronUp, RotateCcw, Edit3, XCircle } from 'lucide-react';

interface FailurePanelProps {
  taskName: string;
  errorOutput: string;
  onRetry: () => void;
  onEditPrompt: () => void;
  onCancel: () => void;
}

export const FailurePanel: React.FC<FailurePanelProps> = ({
  taskName,
  errorOutput,
  onRetry,
  onEditPrompt,
  onCancel,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-zinc-950 border border-red-900/50 rounded-xl overflow-hidden shadow-2xl shadow-red-950/20">
      {/* Alert Header */}
      <div className="bg-red-950/30 border-b border-red-900/30 p-5 flex items-start space-x-3.5">
        <div className="p-2 bg-red-900/25 border border-red-800/30 rounded-lg text-red-400">
          <AlertCircle className="w-6 h-6 animate-pulse" />
        </div>
        <div className="flex-1">
          <h3 className="text-base font-bold text-red-200">
            Build failed at {taskName}
          </h3>
          <p className="text-xs text-red-300/70 mt-1">
            The automated agent encountered errors while executing and testing the changes for this task.
          </p>
        </div>
      </div>

      <div className="p-5 space-y-4">
        {/* Quick Error Summary */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-zinc-400">ERROR OUTPUT SUMMARY</span>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-xs text-zinc-400 hover:text-white flex items-center space-x-1 transition-colors"
            >
              <span>{isExpanded ? 'Hide Details' : 'Show Details'}</span>
              {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          </div>
          
          <pre className="mt-2.5 text-xs text-red-300 font-mono overflow-x-auto whitespace-pre-wrap max-h-32">
            {errorOutput ? errorOutput.split('\n')[0] : 'Unknown error occurred'}
          </pre>

          {isExpanded && (
            <div className="mt-4 pt-4 border-t border-zinc-800">
              <pre className="text-xs font-mono text-zinc-300 bg-black/60 p-3 rounded-lg overflow-x-auto overflow-y-auto max-h-80 whitespace-pre-wrap">
                {errorOutput || 'No details available.'}
              </pre>
            </div>
          )}
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap gap-3">
          <button
            onClick={onRetry}
            className="flex-1 min-w-[150px] flex items-center justify-center space-x-2 py-2.5 px-4 bg-indigo-650 hover:bg-indigo-600 active:bg-indigo-700 text-white text-sm font-semibold rounded-lg shadow-lg shadow-indigo-950/40 transition-all"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Retry Failed Task</span>
          </button>

          <button
            onClick={onEditPrompt}
            className="flex-1 min-w-[150px] flex items-center justify-center space-x-2 py-2.5 px-4 bg-zinc-800 hover:bg-zinc-750 active:bg-zinc-850 text-zinc-200 hover:text-white text-sm font-semibold rounded-lg border border-zinc-700 transition-all"
          >
            <Edit3 className="w-4 h-4" />
            <span>Edit Prompt & Retry</span>
          </button>

          <button
            onClick={onCancel}
            className="w-full sm:w-auto flex items-center justify-center space-x-2 py-2.5 px-4 bg-transparent hover:bg-red-950/20 active:bg-red-950/30 text-red-400 hover:text-red-300 text-sm font-semibold rounded-lg border border-red-950 transition-all"
          >
            <XCircle className="w-4 h-4" />
            <span>Cancel Build</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default FailurePanel;
