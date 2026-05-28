import React, { useState, useEffect, useRef } from "react";
import { Terminal, Activity, Wifi, WifiOff } from "lucide-react";
import { useRunStore } from "../../stores/runStore";

interface RunLogsProps {
  projectId: string;
  backendLogs: string[];
  frontendLogs: string[];
}

type LogTab = "backend" | "frontend" | "install";

export default function RunLogs({ projectId, backendLogs, frontendLogs }: RunLogsProps) {
  const [activeTab, setActiveTab] = useState<LogTab>("backend");
  const installLogs = useRunStore((state) => state.installLogs);
  const connectLogs = useRunStore((state) => state.connectLogs);
  const disconnectLogs = useRunStore((state) => state.disconnectLogs);
  const runStatus = useRunStore((state) => state.runStatus);
  const installStatus = useRunStore((state) => state.installStatus);

  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logic
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [backendLogs, frontendLogs, installLogs, activeTab]);

  // Connect/disconnect SSE stream depending on activeTab and run/install status
  useEffect(() => {
    if (!projectId) return;

    if (activeTab === "install") {
      if (installStatus === "installing") {
        connectLogs(projectId, "install");
      }
    } else {
      if (runStatus === "running" || runStatus === "starting") {
        connectLogs(projectId, activeTab);
      }
    }

    return () => {
      disconnectLogs(activeTab);
    };
  }, [projectId, activeTab, runStatus, installStatus, connectLogs, disconnectLogs]);

  const getLogs = () => {
    if (activeTab === "backend") return backendLogs;
    if (activeTab === "frontend") return frontendLogs;
    return installLogs;
  };

  const isConnected =
    activeTab === "install"
      ? installStatus === "installing"
      : runStatus === "running" || runStatus === "starting";

  const renderLogLine = (line: string, index: number) => {
    const isError =
      line.toLowerCase().includes("error") ||
      line.toLowerCase().includes("fail") ||
      line.toLowerCase().includes("exception") ||
      line.toLowerCase().includes("err:");

    return (
      <div
        key={index}
        className={`whitespace-pre-wrap py-0.5 leading-relaxed font-mono text-xs ${
          isError ? "text-red-400 font-semibold" : "text-slate-300"
        }`}
      >
        {line}
      </div>
    );
  };

  const logs = getLogs();

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg flex flex-col h-[500px]">
      {/* Header and Connection Indicator */}
      <div className="bg-slate-950 px-6 py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800">
        {/* Tabs */}
        <div className="flex space-x-1 bg-slate-900 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setActiveTab("backend")}
            className={`px-4 py-1.5 rounded text-xs font-semibold font-mono transition-all ${
              activeTab === "backend"
                ? "bg-slate-850 text-blue-400 shadow-sm border border-slate-700/50"
                : "text-slate-400 hover:text-slate-200 border border-transparent"
            }`}
          >
            Backend
          </button>
          <button
            onClick={() => setActiveTab("frontend")}
            className={`px-4 py-1.5 rounded text-xs font-semibold font-mono transition-all ${
              activeTab === "frontend"
                ? "bg-slate-850 text-blue-400 shadow-sm border border-slate-700/50"
                : "text-slate-400 hover:text-slate-200 border border-transparent"
            }`}
          >
            Frontend
          </button>
          <button
            onClick={() => setActiveTab("install")}
            className={`px-4 py-1.5 rounded text-xs font-semibold font-mono transition-all ${
              activeTab === "install"
                ? "bg-slate-850 text-blue-400 shadow-sm border border-slate-700/50"
                : "text-slate-400 hover:text-slate-200 border border-transparent"
            }`}
          >
            Installation
          </button>
        </div>

        {/* Connection status indicator */}
        <div className="flex items-center space-x-2">
          {isConnected ? (
            <div className="flex items-center space-x-1.5 text-xs text-emerald-400 font-mono">
              <Wifi className="w-3.5 h-3.5 animate-pulse" />
              <span>Live Streaming</span>
            </div>
          ) : (
            <div className="flex items-center space-x-1.5 text-xs text-slate-500 font-mono">
              <WifiOff className="w-3.5 h-3.5" />
              <span>Disconnected</span>
            </div>
          )}
        </div>
      </div>

      {/* Terminal Content */}
      <div
        ref={containerRef}
        className="flex-1 p-6 overflow-y-auto bg-slate-950 font-mono select-text selection:bg-blue-600/30"
      >
        {logs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-600 space-y-2">
            <Terminal className="w-8 h-8 text-slate-700" />
            <span className="text-xs font-mono">
              No logs captured. Start the process or trigger dependencies install to stream live output.
            </span>
          </div>
        ) : (
          logs.map((line, idx) => renderLogLine(line, idx))
        )}
      </div>
    </div>
  );
}
