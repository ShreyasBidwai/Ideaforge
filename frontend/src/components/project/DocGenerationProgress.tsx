import React from "react";
import { FileText, CheckCircle2, Loader2, Circle } from "lucide-react";

interface DocGenerationProgressProps {
  completedDocs: string[];
  currentDoc: string | null;
  onCancel?: () => void;
}

export const DocGenerationProgress: React.FC<DocGenerationProgressProps> = ({
  completedDocs = [],
  currentDoc = null,
  onCancel,
}) => {
  const docTypes = [
    { key: "architecture", name: "Architecture Document" },
    { key: "prd", name: "Product Requirements Document (PRD)" },
    { key: "trd", name: "Technical Requirements Document (TRD)" },
    { key: "sprint_plan", name: "Sprint Plan" },
    { key: "engineering_standards", name: "Engineering Standards" },
  ];

  const totalDocs = docTypes.length;
  const completedCount = completedDocs.length;
  const progressPercent = Math.round((completedCount / totalDocs) * 100);

  return (
    <div className="w-full bg-slate-900/60 border border-white/5 rounded-2xl p-6 backdrop-blur-xl">
      {/* Header Info */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-4">
        <div>
          <h3 className="text-lg font-bold text-white tracking-wide">
            Generating Documentation Suite
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Gemini AI is crafting your detailed software blueprints
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 px-3 py-1 rounded-full text-xs font-semibold text-blue-400">
            <span>{completedCount}</span>
            <span className="text-blue-500">/</span>
            <span>{totalDocs}</span>
            <span className="text-slate-500 ml-1">({progressPercent}%)</span>
          </div>
          {onCancel && (
            <button
              onClick={onCancel}
              className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 border border-rose-500/25 text-rose-400 hover:bg-rose-500/20 active:bg-rose-500/30 transition-all cursor-pointer"
            >
              <span>Terminate</span>
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-950/60 h-2.5 rounded-full overflow-hidden mb-6 border border-white/5 relative">
        <div
          className="bg-gradient-to-r from-blue-600 to-indigo-500 h-full rounded-full transition-all duration-500 ease-out"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Docs List */}
      <div className="space-y-3">
        {docTypes.map((doc) => {
          const isCompleted = completedDocs.includes(doc.key);
          const isGenerating = currentDoc === doc.key;
          const isPending = !isCompleted && !isGenerating;

          return (
            <div
              key={doc.key}
              className={`flex items-center justify-between p-4 rounded-xl border transition-all duration-300 ${
                isGenerating
                  ? "bg-blue-600/5 border-blue-500/30 shadow-lg shadow-blue-500/5"
                  : isCompleted
                  ? "bg-emerald-500/5 border-emerald-500/10"
                  : "bg-slate-950/20 border-white/5 text-slate-500"
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`p-2 rounded-lg ${
                    isGenerating
                      ? "bg-blue-500/10 text-blue-400"
                      : isCompleted
                      ? "bg-emerald-500/10 text-emerald-400"
                      : "bg-slate-800/40 text-slate-600"
                  }`}
                >
                  <FileText size={18} />
                </div>
                <div>
                  <span
                    className={`text-sm font-semibold tracking-wide block ${
                      isGenerating
                        ? "text-white"
                        : isCompleted
                        ? "text-slate-200"
                        : "text-slate-400"
                    }`}
                  >
                    {doc.name}
                  </span>
                  <span className="text-[10px] text-slate-500 mt-0.5 block">
                    {isGenerating
                      ? "Synthesizing structure concepts..."
                      : isCompleted
                      ? "Complete and ready for review"
                      : "Waiting to generate"}
                  </span>
                </div>
              </div>

              <div>
                {isCompleted ? (
                  <CheckCircle2 className="text-emerald-400 w-5 h-5" />
                ) : isGenerating ? (
                  <Loader2 className="text-blue-400 w-5 h-5 animate-spin" />
                ) : (
                  <Circle className="text-slate-700 w-5 h-5" />
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default DocGenerationProgress;
