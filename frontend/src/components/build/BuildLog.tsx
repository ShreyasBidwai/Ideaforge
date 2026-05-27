import React, { useEffect, useRef } from 'react';
import { Terminal } from 'lucide-react';
import type { BuildLogEntry } from '../../types/api';

interface BuildLogProps {
  logs: BuildLogEntry[];
  isConnected?: boolean;
}

export default function BuildLog({ logs, isConnected = false }: BuildLogProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  const getLogLevelClass = (level: string) => {
    switch (level.toLowerCase()) {
      case "success":
        return "text-emerald-400";
      case "warning":
        return "text-amber-400";
      case "error":
      case "critical":
        return "text-red-400";
      default:
        return "text-blue-400";
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-700/60 rounded-xl overflow-hidden shadow-lg flex flex-col h-[400px]">
      {/* Header */}
      <div className="bg-slate-800/80 px-4 py-3 flex items-center justify-between border-b border-slate-700/60">
        <div className="flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-semibold text-slate-200 font-mono">Live Build Log</span>
        </div>
        <div className="flex items-center space-x-2">
          {isConnected ? (
            <>
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="text-xs text-slate-400 font-mono">Streaming</span>
            </>
          ) : (
            <>
              <span className="inline-flex rounded-full h-2 w-2 bg-slate-600"></span>
              <span className="text-xs text-slate-500 font-mono">Disconnected</span>
            </>
          )}
        </div>
      </div>

      {/* Logs Area */}
      <div
        ref={containerRef}
        className="flex-1 p-4 overflow-y-auto space-y-1.5 font-mono text-xs text-slate-300 bg-slate-950/70"
      >
        {logs.length > 0 ? (
          logs.map((log) => {
            const timeString = log.timestamp
              ? new Date(log.timestamp).toLocaleTimeString()
              : "";
            
            return (
              <div key={log.id} className="flex items-start space-x-2 leading-relaxed">
                <span className="text-slate-600 flex-shrink-0 select-none">
                  [{timeString}]
                </span>
                <span className={`font-semibold flex-shrink-0 select-none ${getLogLevelClass(log.level)}`}>
                  [{log.source}]
                </span>
                <span className="text-slate-300 break-all">{log.message}</span>
              </div>
            );
          })
        ) : (
          <div className="h-full flex items-center justify-center text-slate-600 font-mono">
            Waiting for build to produce logs...
          </div>
        )}
      </div>
    </div>
  );
}
