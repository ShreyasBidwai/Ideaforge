import React from 'react';
import { Play, Pause, XCircle } from 'lucide-react';

interface BuildActionsProps {
  status: string;
  onStart?: () => void;
  onPause: () => void;
  onCancel: () => void;
}

export default function BuildActions({ status, onStart, onPause, onCancel }: BuildActionsProps) {
  const isBuilding = status === "building";
  const isPaused = status === "paused";
  const isRateLimited = status === "rate_limited";

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-800/30 border border-slate-700/50 rounded-xl p-4 backdrop-blur-sm shadow-md">
      <div className="flex items-center space-x-3 w-full sm:w-auto">
        {isBuilding || isRateLimited ? (
          <button
            onClick={onPause}
            className="flex items-center justify-center space-x-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 text-amber-50 rounded-lg text-sm font-semibold transition-colors border border-amber-500/20 shadow w-full sm:w-auto font-mono"
          >
            <Pause className="w-4 h-4" />
            <span>PAUSE</span>
          </button>
        ) : (
          <button
            onClick={onStart}
            className="flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-blue-50 rounded-lg text-sm font-semibold transition-colors border border-blue-500/20 shadow w-full sm:w-auto font-mono"
          >
            <Play className="w-4 h-4" />
            <span>RESUME</span>
          </button>
        )}

        <button
          onClick={onCancel}
          disabled={status === "failed" || status === "complete"}
          className="flex items-center justify-center space-x-2 px-4 py-2 bg-red-600 hover:bg-red-500 text-red-50 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-semibold transition-colors border border-red-500/20 shadow w-full sm:w-auto font-mono"
        >
          <XCircle className="w-4 h-4" />
          <span>CANCEL</span>
        </button>
      </div>

      <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold font-mono">
        Status: <span className={`ml-1 font-bold ${
          status === "complete" ? "text-emerald-400" :
          status === "failed" ? "text-red-500" :
          status === "building" ? "text-blue-400 animate-pulse" :
          status === "rate_limited" ? "text-amber-500 animate-pulse" : "text-slate-400"
        }`}>{status}</span>
      </div>
    </div>
  );
}
