import React, { useState } from "react";
import { Play, Sparkles, Terminal, CheckCircle2, XCircle, HelpCircle, ChevronDown, ChevronUp } from "lucide-react";

export interface E2ETestItem {
  id: string;
  name: string;
  framework: string;
  status: "pending" | "passed" | "failed";
  last_output?: string;
}

interface E2EPanelProps {
  tests: E2ETestItem[];
  runStatus: "stopped" | "running" | "error" | "starting" | "installing";
  onGenerate: () => void | Promise<void>;
  onRun: () => void | Promise<void>;
}

export default function E2EPanel({ tests, runStatus, onGenerate, onRun }: E2EPanelProps) {
  const [expandedTestId, setExpandedTestId] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [running, setRunning] = useState(false);

  const isProjectRunning = runStatus === "running";

  const passedTests = tests.filter((t) => t.status === "passed").length;
  const failedTests = tests.filter((t) => t.status === "failed").length;

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await onGenerate();
    } catch (e) {
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  const handleRun = async () => {
    setRunning(true);
    try {
      await onRun();
    } catch (e) {
      console.error(e);
    } finally {
      setRunning(false);
    }
  };

  const toggleExpand = (id: string) => {
    setExpandedTestId((prev) => (prev === id ? null : id));
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "passed":
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case "failed":
        return <XCircle className="w-4 h-4 text-rose-400" />;
      default:
        return <HelpCircle className="w-4 h-4 text-slate-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "passed":
        return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
      case "failed":
        return "bg-rose-500/10 text-rose-400 border border-rose-500/20";
      default:
        return "bg-slate-800 text-slate-400 border border-slate-700/60";
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
      {/* Top Banner / Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-lg font-bold text-white font-mono uppercase tracking-wider">End-to-End & Integration Testing</h3>
          <p className="text-sm text-slate-400 mt-1">
            Create and run automated functional tests against your running application instance.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white rounded-lg text-xs font-bold transition-all flex items-center space-x-1.5 font-mono shadow-md shadow-blue-600/10"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{generating ? "Generating..." : "Generate E2E Tests"}</span>
          </button>

          <div className="relative group">
            <button
              onClick={handleRun}
              disabled={!isProjectRunning || running || tests.length === 0}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white rounded-lg text-xs font-bold transition-all flex items-center space-x-1.5 font-mono shadow-md shadow-emerald-600/10"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{running ? "Running..." : "Run All"}</span>
            </button>
            {!isProjectRunning && (
              <span className="absolute bottom-full right-0 mb-2 hidden group-hover:block bg-slate-950 text-slate-350 text-[10px] px-2 py-1 rounded border border-slate-800 whitespace-nowrap font-mono shadow-lg">
                Start the project first
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Quote Warning Alert */}
      <div className="bg-amber-500/5 border border-amber-500/10 rounded-lg p-3 flex items-start space-x-3">
        <span className="p-1 bg-amber-500/10 text-amber-400 rounded mt-0.5">
          <Sparkles className="w-3.5 h-3.5" />
        </span>
        <div className="text-xs text-amber-300 leading-relaxed font-mono">
          <strong>Note:</strong> Creating tests uses Claude AI quota. Running the created tests is completely local and free.
        </div>
      </div>

      {/* Results Summary */}
      {tests.length > 0 && (
        <div className="flex items-center space-x-4 bg-slate-950/40 p-4 rounded-lg border border-slate-800/80">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold text-slate-400 font-mono">Results Summary:</span>
            <span className="text-xs font-bold text-emerald-400 font-mono">{passedTests} passed</span>
            <span className="text-slate-650 font-mono">/</span>
            <span className="text-xs font-bold text-rose-450 font-mono">{failedTests} failed</span>
          </div>
        </div>
      )}

      {/* Tests List */}
      <div className="space-y-3">
        {tests.length === 0 ? (
          <div className="text-center py-10 bg-slate-950/20 border border-dashed border-slate-800 rounded-lg">
            <Terminal className="w-8 h-8 text-slate-700 mx-auto mb-2" />
            <p className="text-sm text-slate-500 font-mono">
              No E2E tests created yet. Click the button to create them.
            </p>
          </div>
        ) : (
          tests.map((test) => {
            const isExpanded = expandedTestId === test.id;
            return (
              <div key={test.id} className="border border-slate-800 rounded-lg overflow-hidden bg-slate-950/20">
                {/* Header Row */}
                <div
                  onClick={() => toggleExpand(test.id)}
                  className="p-4 flex items-center justify-between cursor-pointer hover:bg-slate-850/40 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(test.status)}
                    <span className="text-sm font-semibold text-slate-200 font-mono">{test.name}</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className="text-[10px] bg-slate-850 text-slate-400 px-2 py-0.5 rounded font-mono border border-slate-750">
                      {test.framework}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono capitalize ${getStatusBadge(test.status)}`}>
                      {test.status}
                    </span>
                    {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                  </div>
                </div>

                {/* Expanded Console Output */}
                {isExpanded && (
                  <div className="border-t border-slate-850 bg-slate-950 p-4 font-mono text-[11px] text-slate-300 leading-relaxed overflow-x-auto max-h-[300px]">
                    {test.last_output ? (
                      <pre className="whitespace-pre">{test.last_output}</pre>
                    ) : (
                      <span className="text-slate-650 italic">No output captured. Run the test suite to view console logs.</span>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
