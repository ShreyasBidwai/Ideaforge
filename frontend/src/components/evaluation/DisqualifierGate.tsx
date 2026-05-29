import React from "react";
import { CheckCircle, XCircle, AlertTriangle, ArrowRight, RefreshCw } from "lucide-react";
import type { DisqualifierResult } from "../../types/api";

interface DisqualifierGateProps {
  results: DisqualifierResult[] | null;
  error?: string | null;
  onContinue: () => void;
  onRegenerateSolutions?: () => void;
}

const DisqualifierGate: React.FC<DisqualifierGateProps> = ({
  results,
  error,
  onContinue,
  onRegenerateSolutions,
}) => {
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-slate-900 border border-white/5 rounded-2xl text-center space-y-6 max-w-lg mx-auto shadow-xl">
        <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center border border-red-500/20">
          <AlertTriangle className="w-6 h-6 text-red-500" />
        </div>
        <div className="space-y-2">
          <h4 className="text-lg font-bold text-white">Disqualifier Gate Failed</h4>
          <p className="text-slate-400 text-sm leading-relaxed">{error}</p>
        </div>
        {onRegenerateSolutions && (
          <button
            onClick={onRegenerateSolutions}
            className="px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white font-semibold rounded-xl shadow-lg transition-all flex items-center justify-center gap-2"
          >
            <RefreshCw className="w-4 h-4 animate-spin-hover" />
            <span>Regenerate Solutions</span>
          </button>
        )}
      </div>
    );
  }

  if (!results) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-slate-900 border border-white/5 rounded-2xl text-center space-y-4 max-w-lg mx-auto shadow-xl">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-400">Running disqualifier check against gate conditions...</p>
      </div>
    );
  }

  const total = results.length;
  const survivedCount = results.filter((r) => r.passed).length;
  const satisfiesRequirement = survivedCount >= 2;

  return (
    <div className="space-y-6">
      {/* Summary Bar */}
      <div className={`p-6 border rounded-2xl flex flex-col md:flex-row items-center justify-between gap-4 shadow-lg ${
        satisfiesRequirement
          ? "bg-emerald-950/20 border-emerald-500/20 text-emerald-400"
          : "bg-red-950/20 border-red-500/20 text-red-400"
      }`}>
        <div className="space-y-1 text-center md:text-left">
          <h4 className="text-lg font-bold">Disqualifier Gate Summary</h4>
          <p className="text-sm text-slate-300">
            <span>{survivedCount}</span> of <span>{total}</span> solutions survived the disqualifier gate check.
          </p>
        </div>

        {!satisfiesRequirement && (
          <div className="flex items-center gap-2 text-xs bg-red-500/10 border border-red-500/20 px-3 py-1.5 rounded-lg">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <span>At least 2 survivors are required to proceed</span>
          </div>
        )}
      </div>

      {/* Solutions list */}
      <div className="space-y-4">
        {results.map((res, idx) => (
          <div
            key={idx}
            className={`border rounded-2xl p-6 bg-slate-900 shadow-md transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-4 ${
              res.passed
                ? "border-l-4 border-l-emerald-500 border-white/5"
                : "border-l-4 border-l-red-500 border-white/5 opacity-50"
            }`}
          >
            <div className="flex gap-4 items-center">
              <div className="flex-shrink-0">
                {res.passed ? (
                  <CheckCircle className="w-8 h-8 text-emerald-500 fill-emerald-500/10" />
                ) : (
                  <XCircle className="w-8 h-8 text-red-500 fill-red-500/10" />
                )}
              </div>

              <div className="space-y-1">
                <h4 className="font-bold text-white text-lg">{res.solution_title}</h4>
                {!res.passed && res.failed_disqualifiers.length > 0 && (
                  <div className="space-y-1 text-sm">
                    <p className="text-red-400 font-semibold">
                      Failed Gate: {res.failed_disqualifiers.join(", ")}
                    </p>
                    {res.reasons.map((reason, rIdx) => (
                      <p key={rIdx} className="text-slate-400 text-xs">
                        • {reason}
                      </p>
                    ))}
                  </div>
                )}
                {res.passed && (
                  <p className="text-emerald-400/80 text-xs font-semibold">Passed all disqualifier checks</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Warning CTA & Navigation */}
      <div className="pt-6 border-t border-white/5 flex flex-col md:flex-row items-center justify-end gap-4">
        {!satisfiesRequirement && onRegenerateSolutions && (
          <button
            onClick={onRegenerateSolutions}
            className="w-full md:w-auto px-6 py-3 bg-red-600 hover:bg-red-500 text-white font-semibold rounded-xl shadow-lg transition-all flex items-center justify-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Regenerate Solutions</span>
          </button>
        )}

        {satisfiesRequirement && (
          <button
            onClick={onContinue}
            className="w-full md:w-auto px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-blue-500/25 transition-all flex items-center justify-center gap-2"
          >
            <span>Continue to Scoring</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default DisqualifierGate;
