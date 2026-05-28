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

import FailurePanel from "../components/build/FailurePanel";
import QueuePosition from "../components/build/QueuePosition";
import RateLimitCountdown from "../components/build/RateLimitCountdown";
import FileBrowser from "../components/project/FileBrowser";
import apiClient from "../services/api";

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
    currentTask,
    queuePosition,
    failureDetails,
    fetchBuildStatus,
    startBuild,
    pauseBuild,
    cancelBuild,
    connectLogStream,
    disconnectLogStream,
    retryFailed
  } = useBuildStore();

  const [isFullLogOpen, setIsFullLogOpen] = useState(false);
  const [isFileBrowserOpen, setIsFileBrowserOpen] = useState(false);
  const [isPromptEditorOpen, setIsPromptEditorOpen] = useState(false);
  const [editedPrompt, setEditedPrompt] = useState("");
  const [pauseOnFailure, setPauseOnFailure] = useState(false);

  useEffect(() => {
    if (project) {
      setPauseOnFailure(!!project.pause_on_failure);
    }
  }, [project]);

  const handleTogglePauseOnFailure = async () => {
    if (!projectId || !project) return;
    const newValue = !pauseOnFailure;
    setPauseOnFailure(newValue);
    try {
      await apiClient.patch(`/api/v1/projects/${projectId}`, {
        pause_on_failure: newValue,
      });
      fetchBuildStatus(projectId);
    } catch (err) {
      console.error("Failed to update project settings:", err);
      setPauseOnFailure(!newValue);
    }
  };

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

  const handleDownloadProject = () => {
    if (!projectId) return;
    apiClient.get(`/api/v1/projects/${projectId}/download`, { responseType: 'blob' })
      .then((response) => {
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `${project.name || 'project'}.zip`);
        document.body.appendChild(link);
        link.click();
        link.remove();
      })
      .catch((error) => {
        console.error("Failed to download project zip:", error);
      });
  };

  const handleEditPromptSubmit = async () => {
    if (!projectId || !failureDetails?.task_id) return;
    try {
      await apiClient.patch(`/api/v1/tasks/${failureDetails.task_id}/prompt`, { prompt: editedPrompt });
      setIsPromptEditorOpen(false);
      await retryFailed(projectId);
    } catch (err) {
      console.error("Failed to update task prompt and retry:", err);
    }
  };

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

      {/* Build Policy Settings */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="space-y-0.5">
          <h3 className="text-sm font-bold text-slate-200 font-mono">Build Policy Settings</h3>
          <p className="text-xs text-slate-400">Configure orchestrator behavior when task retries or tests fail.</p>
        </div>
        <div className="flex items-center space-x-3">
          <label className="relative inline-flex items-center cursor-pointer select-none">
            <input
              type="checkbox"
              checked={pauseOnFailure}
              onChange={handleTogglePauseOnFailure}
              className="sr-only peer"
              id="pause-on-failure-toggle"
            />
            <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-400 after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-650 peer-checked:after:bg-white peer-checked:after:border-indigo-650"></div>
            <span className="ml-3 text-xs font-semibold text-slate-300 font-mono uppercase tracking-wider">
              {pauseOnFailure ? "Pause Build on Failure" : "Skip Failed & Auto-Heal"}
            </span>
          </label>
        </div>
      </div>

      {/* Dynamic Recovery Panels */}
      {status === "failed" && (
        <FailurePanel
          taskName={failureDetails?.name || currentTask?.name || "Task"}
          errorOutput={failureDetails?.error_output || currentTask?.error_output || "No error output details available."}
          onRetry={() => retryFailed(projectId!)}
          onEditPrompt={() => {
            setEditedPrompt(failureDetails?.prompt || currentTask?.prompt || "");
            setIsPromptEditorOpen(true);
          }}
          onCancel={() => cancelBuild(projectId!)}
        />
      )}

      {status === "queued" && (
        <QueuePosition
          position={queuePosition || 1}
          estimatedWait={queuePosition ? `~${queuePosition * 2} hours` : "~2 hours"}
          onCancel={() => cancelBuild(projectId!)}
        />
      )}

      {status === "rate_limited" && rateLimitInfo?.resumeAt && (
        <RateLimitCountdown resumeAt={currentTask?.rate_limit_reset_at || rateLimitInfo.resumeAt} />
      )}

      {/* Code Access Panel */}
      {(status === "complete" || status === "building" || status === "failed") && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-slate-200 font-mono">Workspace Code Access</h3>
            <p className="text-xs text-slate-400">Examine built files directly or download the full workspace bundle.</p>
          </div>
          <div className="flex items-center space-x-3 w-full md:w-auto">
            <button
              onClick={() => setIsFileBrowserOpen(true)}
              className="flex-1 md:flex-none flex items-center justify-center space-x-2 py-2 px-4 bg-zinc-800 hover:bg-zinc-750 text-zinc-100 hover:text-white font-semibold text-xs rounded-lg border border-zinc-700 transition-all font-mono"
            >
              <span>BROWSE CODE</span>
            </button>
            <button
              onClick={handleDownloadProject}
              className="flex-1 md:flex-none flex items-center justify-center space-x-2 py-2 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-lg transition-all font-mono"
            >
              <span>DOWNLOAD PROJECT</span>
            </button>
          </div>
        </div>
      )}

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

      {/* File Browser Overlay */}
      {isFileBrowserOpen && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/85 backdrop-blur-xs">
          <div className="bg-slate-900 border-l border-slate-800 w-full max-w-5xl h-screen flex flex-col shadow-2xl">
            <div className="bg-slate-950 px-6 py-4 flex items-center justify-between border-b border-slate-850">
              <div className="space-y-0.5">
                <span className="text-sm font-bold text-white font-mono uppercase tracking-wider">Workspace Code Explorer</span>
                <p className="text-[10px] text-slate-500 font-mono">Exploring source files inside project directory</p>
              </div>
              <button
                onClick={() => setIsFileBrowserOpen(false)}
                className="text-xs text-slate-400 hover:text-white font-bold font-mono px-3 py-1.5 rounded-lg border border-slate-850 hover:bg-slate-900 transition-all"
              >
                CLOSE EXPLORER
              </button>
            </div>
            <div className="flex-1 overflow-hidden p-6 bg-slate-900/40">
              <FileBrowser projectId={projectId!} />
            </div>
          </div>
        </div>
      )}

      {/* Prompt Editor Modal */}
      {isPromptEditorOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xs">
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl flex flex-col w-full max-w-2xl">
            <div className="bg-slate-950/80 px-6 py-4 flex items-center justify-between border-b border-slate-800">
              <span className="text-sm font-bold text-zinc-200 font-mono">Edit Prompt & Retry</span>
              <button
                onClick={() => setIsPromptEditorOpen(false)}
                className="text-xs text-zinc-400 hover:text-zinc-200 font-bold font-mono"
              >
                CLOSE
              </button>
            </div>
            <div className="p-6 space-y-4">
              <label className="block text-xs font-mono text-zinc-400 uppercase tracking-wider">Task Prompt</label>
              <textarea
                value={editedPrompt}
                onChange={(e) => setEditedPrompt(e.target.value)}
                className="w-full h-80 bg-zinc-950 border border-zinc-800 rounded-lg p-3 text-xs font-mono text-zinc-300 focus:outline-none focus:border-indigo-500"
              />
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setIsPromptEditorOpen(false)}
                  className="px-4 py-2 bg-transparent hover:bg-zinc-800 text-zinc-300 text-xs font-bold font-mono rounded-lg transition-colors border border-zinc-800"
                >
                  CANCEL
                </button>
                <button
                  onClick={handleEditPromptSubmit}
                  className="px-4 py-2 bg-indigo-650 hover:bg-indigo-600 text-white text-xs font-bold font-mono rounded-lg transition-colors shadow-lg shadow-indigo-950/40"
                >
                  SAVE & RETRY
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
