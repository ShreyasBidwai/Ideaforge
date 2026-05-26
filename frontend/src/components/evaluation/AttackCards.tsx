import React from "react";
import { Check, X, ShieldAlert } from "lucide-react";
import type { AttackResult } from "../../types/api";

interface AttackCardsProps {
  attacks: AttackResult[] | null;
  onContinue?: () => void;
  continueText?: string;
}

const AttackCards: React.FC<AttackCardsProps> = ({
  attacks,
  onContinue,
  continueText = "Continue to ACH",
}) => {
  if (!attacks) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-slate-900 border border-white/5 rounded-2xl text-center space-y-4 max-w-lg mx-auto shadow-xl">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-400">Generating minimax attack scenario cards...</p>
      </div>
    );
  }

  const getSeverityBadgeClass = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "high":
        return "bg-red-500/10 text-red-400 border-red-500/20";
      case "medium":
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      default:
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {attacks.map((att) => {
          const survives = att.survives;

          return (
            <div
              key={att.solution_title}
              className={`border rounded-2xl p-6 bg-slate-900 shadow-lg relative space-y-6 flex flex-col justify-between transition-all ${
                survives
                  ? "border-white/5"
                  : "border-red-500/20 bg-red-950/5"
              }`}
            >
              <div className="space-y-4">
                {/* Header */}
                <div className="flex items-start justify-between gap-3">
                  <h4 className="text-lg font-bold text-white">{att.solution_title}</h4>
                  <span className={`text-xs px-2.5 py-1 rounded-full border font-semibold capitalize ${getSeverityBadgeClass(att.severity)}`}>
                    {att.severity} Severity
                  </span>
                </div>

                {/* Attack Text */}
                <div className="bg-red-950/20 border-l-4 border-red-500/50 p-4 rounded-xl space-y-2">
                  <div className="flex items-center gap-1.5 text-xs text-red-400 font-bold uppercase tracking-wider">
                    <ShieldAlert className="w-3.5 h-3.5" />
                    <span>Steelman Attack Critique</span>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {att.attack}
                  </p>
                </div>
              </div>

              {/* Survival Verdict */}
              <div className="pt-4 border-t border-white/5 flex gap-3 items-start">
                <div className={`p-2 rounded-xl border flex-shrink-0 ${
                  survives
                    ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                    : "bg-red-500/10 border-red-500/20 text-red-400"
                }`}>
                  {survives ? <Check className="w-5 h-5" /> : <X className="w-5 h-5" />}
                </div>

                <div className="space-y-0.5">
                  <p className="text-sm font-semibold text-white">
                    {survives ? "Survives Attack Scenario" : "Critically Weakened"}
                  </p>
                  {att.survival_reasoning && (
                    <p className="text-xs text-slate-400">
                      {att.survival_reasoning}
                    </p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {onContinue && (
        <div className="flex justify-end pt-4">
          <button
            onClick={onContinue}
            className="w-full md:w-auto px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-blue-500/25 transition-all flex items-center justify-center gap-2"
          >
            <span>{continueText}</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default AttackCards;
