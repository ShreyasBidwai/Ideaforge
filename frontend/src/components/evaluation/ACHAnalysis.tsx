import React from "react";
import { AlertCircle, HelpCircle } from "lucide-react";
import type { ACHResult } from "../../types/api";

interface ACHAnalysisProps {
  analysis: ACHResult[] | null;
  onContinue?: () => void;
}

const ACHAnalysis: React.FC<ACHAnalysisProps> = ({
  analysis,
  onContinue,
}) => {
  if (!analysis) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-slate-900 border border-white/5 rounded-2xl text-center space-y-4 max-w-lg mx-auto shadow-xl">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-400">Running ACH Analysis and checking evidence inconsistencies...</p>
      </div>
    );
  }

  // Sort solutions by inconsistency count ascending (best first)
  const sortedAnalysis = [...analysis].sort((a, b) => a.count - b.count);

  const getBadgeColor = (count: number) => {
    if (count === 0) return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    if (count <= 2) return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    return "bg-red-500/10 text-red-400 border-red-500/20";
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {sortedAnalysis.map((sol) => (
          <div
            key={sol.solution_title}
            className="border border-white/5 rounded-2xl p-6 bg-slate-900 shadow-lg flex flex-col justify-between space-y-4 hover:border-white/10 transition-all"
          >
            <div className="space-y-4">
              {/* Header */}
              <div className="flex items-center justify-between gap-3 border-b border-white/5 pb-3">
                <h4 className="text-lg font-bold text-white">{sol.solution_title}</h4>
                <div className={`w-8 h-8 flex items-center justify-center rounded-full border text-sm font-bold ${getBadgeColor(sol.count)}`}>
                  {sol.count}
                </div>
              </div>

              {/* Inconsistencies List */}
              {sol.count === 0 ? (
                <div className="text-center py-4">
                  <p className="text-sm font-semibold text-emerald-400">No inconsistencies found</p>
                  <p className="text-xs text-slate-500 mt-1">Fully consistent with problem constraints</p>
                </div>
              ) : (
                <ul className="space-y-2">
                  {sol.inconsistencies.map((inc, iIdx) => (
                    <li key={iIdx} className="flex gap-2 items-start text-sm text-slate-300">
                      <div className="p-0.5 mt-0.5 bg-red-500/10 text-red-400 rounded">
                        <AlertCircle className="w-3.5 h-3.5" />
                      </div>
                      <span className="leading-relaxed">{inc}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        ))}
      </div>

      {onContinue && (
        <div className="flex justify-end pt-4">
          <button
            onClick={onContinue}
            className="w-full md:w-auto px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-blue-500/25 transition-all flex items-center justify-center gap-2"
          >
            <span>Generate Final Comparison</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default ACHAnalysis;
