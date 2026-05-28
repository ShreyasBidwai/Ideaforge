import React from "react";
import { Play, Square, RefreshCw, Activity, ArrowUpRight } from "lucide-react";

interface RunPanelProps {
  ready: boolean;
  installed: boolean;
  status: "stopped" | "running" | "error" | "starting" | "installing";
  backendUrl?: string | null;
  frontendUrl?: string | null;
  onInstall: () => void | Promise<void>;
  onStart: () => void | Promise<void>;
  onStop: () => void | Promise<void>;
}

export default function RunPanel({
  ready,
  installed,
  status,
  backendUrl,
  frontendUrl,
  onInstall,
  onStart,
  onStop,
}: RunPanelProps) {
  const getStatusBadge = () => {
    switch (status) {
      case "running":
        return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
      case "starting":
        return "bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse";
      case "installing":
        return "bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse";
      case "error":
        return "bg-rose-500/10 text-rose-400 border border-rose-500/20";
      default:
        return "bg-slate-800 text-slate-400 border border-slate-700/60";
    }
  };

  const isInstalling = status === "installing";
  const isRunning = status === "running" || status === "starting";

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
      {/* Title & Status */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-lg font-bold text-white font-mono uppercase tracking-wider">Process Manager</h3>
          <p className="text-sm text-slate-400 mt-1">
            Manage running processes and application controls.
          </p>
        </div>
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold font-mono capitalize ${getStatusBadge()}`}>
          {status}
        </span>
      </div>

      {/* Control Buttons */}
      <div className="flex flex-wrap gap-4">
        <button
          onClick={onInstall}
          disabled={isRunning || isInstalling}
          className="px-5 py-2.5 bg-slate-800 hover:bg-slate-705 disabled:opacity-40 text-slate-200 border border-slate-700 rounded-lg text-sm font-semibold transition-all flex items-center space-x-2 font-mono shadow-md"
        >
          <RefreshCw className={`w-4 h-4 ${isInstalling ? "animate-spin" : ""}`} />
          <span>Install Dependencies</span>
        </button>

        <button
          onClick={onStart}
          disabled={!ready || !installed || isRunning || isInstalling}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white rounded-lg text-sm font-semibold transition-all flex items-center space-x-2 border border-blue-500/20 shadow-md font-mono shadow-blue-600/10"
        >
          <Play className="w-4 h-4" />
          <span>Start Project</span>
        </button>

        <button
          onClick={onStop}
          disabled={!isRunning}
          className="px-5 py-2.5 bg-rose-600/10 hover:bg-rose-600/20 disabled:opacity-40 text-rose-450 border border-rose-500/20 rounded-lg text-sm font-semibold transition-all flex items-center space-x-2 font-mono"
        >
          <Square className="w-4 h-4" />
          <span>Stop</span>
        </button>
      </div>

      {/* Running Info */}
      {status === "running" && (backendUrl || frontendUrl) && (
        <div className="bg-slate-950/60 border border-slate-850 rounded-lg p-4 space-y-3">
          <h4 className="text-xs font-semibold text-slate-500 font-mono uppercase tracking-wider">Running Project URLs</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {backendUrl && (
              <a
                href={backendUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-3 bg-slate-900 border border-slate-800 rounded hover:border-blue-550/40 transition-all group"
              >
                <div>
                  <span className="text-[10px] text-slate-500 font-mono uppercase block">Backend Server</span>
                  <span className="text-xs font-semibold text-blue-400 group-hover:text-blue-300 font-mono break-all">
                    {backendUrl}
                  </span>
                </div>
                <ArrowUpRight className="w-4 h-4 text-slate-500 group-hover:text-blue-400 transition-colors" />
              </a>
            )}
            {frontendUrl && (
              <a
                href={frontendUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-3 bg-slate-900 border border-slate-800 rounded hover:border-blue-550/40 transition-all group"
              >
                <div>
                  <span className="text-[10px] text-slate-500 font-mono uppercase block">Frontend App</span>
                  <span className="text-xs font-semibold text-blue-400 group-hover:text-blue-300 font-mono break-all">
                    {frontendUrl}
                  </span>
                </div>
                <ArrowUpRight className="w-4 h-4 text-slate-500 group-hover:text-blue-400 transition-colors" />
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
