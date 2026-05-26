import React, { useState } from "react";
import type { ScoringResult, RubricCriterion } from "../../types/api";

interface ScoringTableProps {
  scores: ScoringResult[] | null;
  criteria: Pick<RubricCriterion, "name" | "weight">[];
  onContinue?: () => void;
}

const ScoringTable: React.FC<ScoringTableProps> = ({
  scores,
  criteria,
  onContinue,
}) => {
  const [highlightedCol, setHighlightedCol] = useState<string | null>(null);

  if (!scores) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-slate-900 border border-white/5 rounded-2xl text-center space-y-4 max-w-lg mx-auto shadow-xl">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-400">Evaluating and scoring candidate solutions...</p>
      </div>
    );
  }

  const getScoreColorClass = (score: number) => {
    if (score <= 2) return "bg-red-500/10 text-red-400 border-red-500/20";
    if (score === 3) return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
  };

  return (
    <div className="space-y-6">
      <div className="overflow-x-auto border border-white/5 rounded-2xl shadow-xl bg-slate-900/60 max-w-full">
        <table className="w-full border-collapse text-left min-w-[600px]">
          <thead>
            <tr className="border-b border-white/5 bg-slate-900/80">
              <th className="p-4 font-semibold text-slate-400 sticky left-0 bg-slate-900/90 z-10 w-[200px]">
                Evaluation Criterion
              </th>
              {scores.map((sol) => (
                <th
                  key={sol.solution_title}
                  onClick={() =>
                    setHighlightedCol(
                      highlightedCol === sol.solution_title ? null : sol.solution_title
                    )
                  }
                  className={`p-4 font-bold text-white text-center cursor-pointer select-none transition-colors border-l border-white/5 hover:bg-slate-800 ${
                    highlightedCol === sol.solution_title ? "bg-blue-600/20 text-blue-400" : ""
                  }`}
                >
                  {sol.solution_title}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {criteria.map((crit) => (
              <tr key={crit.name} className="border-b border-white/5 hover:bg-slate-800/40">
                <td className="p-4 font-medium text-slate-300 sticky left-0 bg-slate-900/90 z-10 border-r border-white/5">
                  <div className="flex flex-col">
                    <span className="font-semibold text-white">{crit.name}</span>
                    <span className="text-xs text-slate-500">Weight: {crit.weight}x</span>
                  </div>
                </td>
                {scores.map((sol) => {
                  const scoreObj = sol.criterion_scores.find(
                    (cs) => cs.criterion.toLowerCase() === crit.name.toLowerCase()
                  );
                  const score = scoreObj ? scoreObj.score : 0;
                  const justification = scoreObj ? scoreObj.justification : "";

                  return (
                    <td
                      key={sol.solution_title}
                      className={`p-4 text-center border-l border-white/5 transition-colors relative group ${
                        highlightedCol === sol.solution_title ? "bg-blue-600/5" : ""
                      }`}
                    >
                      <div className={`inline-flex items-center justify-center w-10 h-10 rounded-xl border font-bold text-sm ${getScoreColorClass(score)}`}>
                        {score}
                      </div>

                      {justification && (
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-20 w-48 bg-slate-950 text-slate-200 border border-white/10 rounded-lg p-2.5 text-xs shadow-2xl text-left pointer-events-none">
                          {justification}
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}

            {/* Weighted Average */}
            <tr className="border-b border-white/5 bg-slate-900/40">
              <td className="p-4 font-bold text-slate-300 sticky left-0 bg-slate-900/90 z-10 border-r border-white/5">
                Weighted Average
              </td>
              {scores.map((sol) => (
                <td
                  key={sol.solution_title}
                  className={`p-4 text-center border-l border-white/5 font-bold transition-colors text-white ${
                    highlightedCol === sol.solution_title ? "bg-blue-600/10 text-blue-400" : ""
                  }`}
                >
                  {sol.weighted_avg ? sol.weighted_avg.toFixed(2) : "0.00"}
                </td>
              ))}
            </tr>

            {/* Min Score */}
            <tr className="bg-slate-900/40">
              <td className="p-4 font-bold text-slate-300 sticky left-0 bg-slate-900/90 z-10 border-r border-white/5">
                Minimum Score
              </td>
              {scores.map((sol) => (
                <td
                  key={sol.solution_title}
                  className={`p-4 text-center border-l border-white/5 font-bold transition-colors ${
                    sol.min_score <= 2
                      ? "text-red-400"
                      : "text-white"
                  } ${highlightedCol === sol.solution_title ? "bg-blue-600/10" : ""}`}
                >
                  {sol.min_score || 0}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      {onContinue && (
        <div className="flex justify-end pt-4">
          <button
            onClick={onContinue}
            className="w-full md:w-auto px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-blue-500/25 transition-all flex items-center justify-center gap-2"
          >
            <span>Continue to Devil's Advocate</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default ScoringTable;
