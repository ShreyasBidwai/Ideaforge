import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ChevronLeft } from "lucide-react";
import { useBuildStore } from "../stores/buildStore";
import BuildStats from "../components/build/BuildStats";
import BuildProgress from "../components/build/BuildProgress";
import RateLimitGauge from "../components/build/RateLimitGauge";
import SprintAccordion from "../components/build/SprintAccordion";
import BuildLog from "../components/build/BuildLog";
import BuildActions from "../components/build/BuildActions";

export default function BuildDashboard() {
  const { projectId } = useParams<{ projectId: string }>();
  const {
    project,
    sprints,
    logs,
    status,
    stats,
    rateLimitInfo,
    isConnected,
    fetchBuildStatus,
    startBuild,
    pauseBuild,
    cancelBuild,
    connectLogStream,
    disconnectLogStream
  } = useBuildStore();

  const [isFullLogOpen, setIsFullLogOpen] = useState(false);

  useEffect(() => {
    if (!projectId) return;

    fetchBuildStatus(projectId);
    connectLogStream(projectId);

    const interval = setInterval(() => {
      fetchBuildStatus(projectId);
    }, 5000);

    return () => {
      clearInterval(interval);
      disconnectLogStream();
    };
  }, [projectId, fetchBuildStatus, connectLogStream, disconnectLogStream]);

  if (!project) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-slate-400 font-mono">
        Loading project build status...
      </div>
    );
  }

  const overallProgress = stats.totalTasks > 0 ? (stats.completedTasks / stats.totalTasks) * 100 : 0;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-6 lg:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <Link
            to="/approvals"
            className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors font-mono mb-2"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            <span>BACK TO APPROVALS</span>
          </Link>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white">{project.name}</h1>
            {status === "building" && (
              <span className="flex items-center space-x-1.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full text-xs font-semibold animate-pulse font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                <span>BUILDING</span>
              </span>
            )}
            {status === "paused" && (
              <span className="flex items-center space-x-1.5 bg-slate-800 text-slate-400 border border-slate-700/60 px-2 py-0.5 rounded-full text-xs font-semibold font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-500"></span>
                <span>PAUSED</span>
              </span>
            )}
            {status === "complete" && (
              <span className="flex items-center space-x-1.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full text-xs font-semibold font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                <span>COMPLETE</span>
              </span>
            )}
            {status === "failed" && (
              <span className="flex items-center space-x-1.5 bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 rounded-full text-xs font-semibold font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400"></span>
                <span>FAILED</span>
              </span>
            )}
            {status === "rate_limited" && (
              <span className="flex items-center space-x-1.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded-full text-xs font-semibold font-mono animate-pulse">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                <span>RATE LIMITED</span>
              </span>
            )}
          </div>
          <p className="text-sm text-slate-400 mt-1">Real-time status of software construction pipeline.</p>
        </div>
        
        {projectId && (
          <BuildActions
            status={status}
            onStart={() => startBuild(projectId)}
            onPause={() => pauseBuild(projectId)}
            onCancel={() => cancelBuild(projectId)}
          />
        )}
      </div>

      {/* Stats Cards */}
      <BuildStats stats={stats} />

      {/* Progress & Rate Limit */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <BuildProgress progress={overallProgress} />
        </div>
        <div>
          <RateLimitGauge info={rateLimitInfo} />
        </div>
      </div>

      {/* Sprints & Logs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h2 className="text-base font-semibold text-slate-200 font-mono">Sprint Breakdown</h2>
          <SprintAccordion sprints={sprints} />
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-200 font-mono">Build Activity</h2>
            <button
              onClick={() => setIsFullLogOpen(true)}
              className="text-xs text-blue-400 hover:text-blue-300 font-semibold font-mono"
            >
              FULL LOG
            </button>
          </div>
          <BuildLog logs={logs} isConnected={isConnected} />
        </div>
      </div>

      {/* Full Log Modal */}
      {isFullLogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-700/60 rounded-xl overflow-hidden shadow-2xl flex flex-col w-full max-w-4xl h-[80vh]">
            <div className="bg-slate-800/80 px-6 py-4 flex items-center justify-between border-b border-slate-700/60">
              <span className="text-sm font-bold text-slate-200 font-mono">Expanded Build Log</span>
              <button
                onClick={() => setIsFullLogOpen(false)}
                className="text-xs text-slate-400 hover:text-slate-200 font-bold font-mono"
              >
                CLOSE
              </button>
            </div>
            <div className="flex-1 p-6 overflow-y-auto space-y-1.5 font-mono text-xs text-slate-300 bg-slate-950/90">
              {logs.map((log) => {
                const timeString = log.timestamp
                  ? new Date(log.timestamp).toLocaleString()
                  : "";
                
                return (
                  <div key={log.id} className="flex items-start space-x-2 leading-relaxed">
                    <span className="text-slate-600 flex-shrink-0 select-none">
                      [{timeString}]
                    </span>
                    <span className="text-blue-400 font-semibold flex-shrink-0 select-none font-mono">
                      [{log.source}]
                    </span>
                    <span className="text-slate-300 break-all">{log.message}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
