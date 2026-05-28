import React, { useEffect, useRef, useState } from 'react';
import { Terminal, ChevronDown, ChevronRight, Bot, FlaskConical, Send } from 'lucide-react';
import type { BuildLogEntry } from '../../types/api';

interface BuildLogProps {
  logs: BuildLogEntry[];
  isConnected?: boolean;
}

function ExpandableLog({ log, timeString }: { log: BuildLogEntry; timeString: string }) {
  const [expanded, setExpanded] = useState(false);
  const isExpandable = log.level === 'PROMPT' || log.level === 'CLAUDE' || log.level === 'TESTS';
  const preview = log.message.slice(0, 120) + (log.message.length > 120 ? '...' : '');

  if (!isExpandable) return null;

  const config = {
    PROMPT: {
      icon: <Send className="w-3.5 h-3.5" />,
      label: '↑ PROMPT SENT',
      headerClass: 'bg-violet-950/60 border-violet-700/40 text-violet-300',
      bodyClass: 'bg-violet-950/30 text-violet-200/80 border-violet-700/30',
      badgeClass: 'bg-violet-900/60 text-violet-300',
    },
    CLAUDE: {
      icon: <Bot className="w-3.5 h-3.5" />,
      label: '↓ CLAUDE RESPONSE',
      headerClass: 'bg-emerald-950/60 border-emerald-700/40 text-emerald-300',
      bodyClass: 'bg-emerald-950/30 text-emerald-200/80 border-emerald-700/30',
      badgeClass: 'bg-emerald-900/60 text-emerald-300',
    },
    TESTS: {
      icon: <FlaskConical className="w-3.5 h-3.5" />,
      label: '⚗ TEST RESULTS',
      headerClass: 'bg-sky-950/60 border-sky-700/40 text-sky-300',
      bodyClass: 'bg-sky-950/30 text-sky-200/80 border-sky-700/30',
      badgeClass: 'bg-sky-900/60 text-sky-300',
    },
  }[log.level] ?? null;

  if (!config) return null;

  return (
    <div className={`rounded-lg border overflow-hidden my-2 ${config.headerClass}`}>
      <button
        onClick={() => setExpanded(!expanded)}
        className={`w-full flex items-center justify-between px-3 py-2 text-xs font-mono font-semibold ${config.headerClass} hover:opacity-90 transition-opacity`}
      >
        <div className="flex items-center space-x-2">
          {config.icon}
          <span>{config.label}</span>
          <span className="text-slate-500 font-normal">{log.source}</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-slate-500 font-normal">{timeString}</span>
          {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        </div>
      </button>
      {!expanded && (
        <div className={`px-3 py-1.5 text-xs border-t ${config.bodyClass} opacity-70 truncate`}>
          {preview}
        </div>
      )}
      {expanded && (
        <pre className={`px-3 py-2 text-xs border-t ${config.bodyClass} whitespace-pre-wrap break-words max-h-96 overflow-y-auto`}>
          {log.message}
        </pre>
      )}
    </div>
  );
}

export default function BuildLog({ logs, isConnected = false }: BuildLogProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  const getLogLevelStyle = (level: string) => {
    switch (level.toUpperCase()) {
      case 'SUCCESS':   return 'text-emerald-400';
      case 'WARNING':   return 'text-amber-400';
      case 'ERROR':
      case 'CRITICAL':  return 'text-red-400';
      case 'PROMPT':    return 'text-violet-400';
      case 'CLAUDE':    return 'text-emerald-300';
      case 'TESTS':     return 'text-sky-400';
      default:          return 'text-blue-400';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-700/60 rounded-xl overflow-hidden shadow-lg flex flex-col h-[550px]">
      {/* Header */}
      <div className="bg-slate-800/80 px-4 py-3 flex items-center justify-between border-b border-slate-700/60">
        <div className="flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-semibold text-slate-200 font-mono">Live Build Log</span>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs font-mono text-slate-500">
            <span className="w-2 h-2 rounded-full bg-violet-500 inline-block" />PROMPT
            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block ml-2" />CLAUDE
            <span className="w-2 h-2 rounded-full bg-sky-500 inline-block ml-2" />TESTS
          </div>
          {isConnected ? (
            <>
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <span className="text-xs text-slate-400 font-mono">Streaming</span>
            </>
          ) : (
            <>
              <span className="inline-flex rounded-full h-2 w-2 bg-slate-600" />
              <span className="text-xs text-slate-500 font-mono">Disconnected</span>
            </>
          )}
        </div>
      </div>

      {/* Logs Area */}
      <div
        ref={containerRef}
        className="flex-1 p-3 overflow-y-auto font-mono text-xs text-slate-300 bg-slate-950/70 space-y-0.5"
      >
        {logs.length > 0 ? (
          logs.map((log) => {
            const timeString = log.timestamp
              ? new Date(log.timestamp).toLocaleTimeString()
              : '';

            // Expandable rich entries
            if (['PROMPT', 'CLAUDE', 'TESTS'].includes(log.level)) {
              return <ExpandableLog key={log.id} log={log} timeString={timeString} />;
            }

            // Standard log line
            return (
              <div key={log.id} className="flex items-start space-x-2 leading-relaxed py-0.5">
                <span className="text-slate-600 flex-shrink-0 select-none">[{timeString}]</span>
                <span className={`font-semibold flex-shrink-0 select-none ${getLogLevelStyle(log.level)}`}>
                  [{log.level}]
                </span>
                <span className="text-slate-500 flex-shrink-0 select-none">[{log.source}]</span>
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
