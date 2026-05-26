import React, { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Check, X, ShieldAlert, Award, Star, RefreshCw, ArrowRight } from "lucide-react";
import type { ComparisonResult } from "../../types/api";
import MetricLeaderBadge from "./MetricLeaderBadge";

interface ComparisonMatrixProps {
  comparison: ComparisonResult | null;
  onApprove: (solutionId: string) => void;
  onRegenerateSolutions?: () => void;
}

const ComparisonMatrix: React.FC<ComparisonMatrixProps> = ({
  comparison,
  onApprove,
  onRegenerateSolutions,
}) => {
  const [approvedSolutionId, setApprovedSolutionId] = useState<string | null>(null);
  const [showConfetti, setShowConfetti] = useState(false);
  const [expandedAttacks, setExpandedAttacks] = useState<Record<string, boolean>>({});

  if (!comparison) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-slate-900 border border-white/5 rounded-2xl text-center space-y-4 max-w-lg mx-auto shadow-xl">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-400">Compiling and generating comparison matrix...</p>
      </div>
    );
  }

  const handleApprove = async (solId: string) => {
    const previous = approvedSolutionId;
    setApprovedSolutionId(solId);
    setShowConfetti(true);
    try {
      await onApprove(solId);
    } catch (err) {
      setApprovedSolutionId(previous);
      setShowConfetti(false);
    }
    setTimeout(() => {
      setShowConfetti(false);
    }, 2500);
  };

  const toggleExpand = (title: string) => {
    setExpandedAttacks((prev) => ({
      ...prev,
      [title]: !prev[title],
    }));
  };

  // Helper to extract leaders safely
  const scoreLeader = comparison.leaders["weighted_avg"] || "";
  const attackLeader = comparison.leaders["attack_survival"] || comparison.leaders["attack_survives"] || "";
  const minScoreLeader = comparison.leaders["min_score"] || "";
  const inconsistencyLeader = comparison.leaders["inconsistencies"] || comparison.leaders["inconsistency_count"] || "";

  const clearWinnerTitle = comparison.is_clear_winner ? scoreLeader : null;

  // Maximum inconsistency count for bar scaling
  const maxInconsistencies = Math.max(
    ...comparison.entries.map((e) => e.inconsistency_count),
    1
  );

  return (
    <div className="space-y-8 relative">
      {/* Tasteful Framer Motion Confetti */}
      {showConfetti && (
        <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
          {[...Array(60)].map((_, i) => {
            const x = Math.random() * 100;
            const delay = Math.random() * 0.4;
            const duration = 1.2 + Math.random() * 1.5;
            const size = 6 + Math.random() * 8;
            const color = ["#10B981", "#3B82F6", "#F59E0B", "#EF4444", "#EC4899"][
              Math.floor(Math.random() * 5)
            ];

            return (
              <motion.div
                key={i}
                initial={{ y: -20, x: `${x}vw`, opacity: 1, rotate: 0 }}
                animate={{ y: "110vh", opacity: 0, rotate: 360 }}
                transition={{ duration, delay, ease: "easeOut" }}
                style={{
                  position: "absolute",
                  width: size,
                  height: size,
                  backgroundColor: color,
                  borderRadius: Math.random() > 0.5 ? "50%" : "2px",
                }}
              />
            );
          })}
        </div>
      )}

      {/* Clear Winner Banner */}
      {comparison.is_clear_winner && clearWinnerTitle && (
        <div className="bg-emerald-950/30 border border-emerald-500/30 text-emerald-400 p-6 rounded-2xl flex items-center gap-4 shadow-xl">
          <div className="p-3 bg-emerald-500/10 rounded-full border border-emerald-500/20">
            <Award className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h4 className="font-bold text-white text-base">Clear Winner</h4>
            <p className="text-sm text-slate-300 mt-0.5">
              Clear survivor: <span className="font-bold text-emerald-400">{clearWinnerTitle}</span> leads on all metrics.
            </p>
          </div>
        </div>
      )}

      {/* Disagreement Alert Banner */}
      {!comparison.is_clear_winner && (
        <div className="bg-amber-950/20 border border-amber-500/25 text-amber-400 p-6 rounded-2xl space-y-4 shadow-xl">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-amber-500/10 rounded-full border border-amber-500/20 flex-shrink-0">
              <ShieldAlert className="w-6 h-6 text-amber-400" />
            </div>
            <div>
              <h4 className="font-bold text-white text-base">Metrics Disagree</h4>
              <p className="text-sm text-slate-300 mt-1">
                Metrics disagree — <span className="font-semibold text-amber-300">{scoreLeader}</span> leads on score but{" "}
                <span className="font-semibold text-amber-300">{attackLeader || inconsistencyLeader}</span> survives attacks better. Review carefully before deciding.
              </p>
            </div>
          </div>
          <div className="pl-16 space-y-1.5 text-xs text-slate-400">
            <p className="font-semibold text-slate-300 uppercase tracking-wider mb-1">Leaders List:</p>
            {scoreLeader && <p>• Weighted Average: <span className="text-white font-medium">{scoreLeader}</span></p>}
            {minScoreLeader && <p>• Minimum Score: <span className="text-white font-medium">{minScoreLeader}</span></p>}
            {attackLeader && <p>• Devil's Advocate Survival: <span className="text-white font-medium">{attackLeader}</span></p>}
            {inconsistencyLeader && <p>• Inconsistency Count: <span className="text-white font-medium">{inconsistencyLeader}</span></p>}
          </div>
        </div>
      )}

      {/* Comparison Table */}
      <div className="overflow-x-auto border border-white/5 rounded-2xl shadow-2xl bg-slate-900/60 max-w-full">
        <table className="w-full border-collapse text-left min-w-[750px]">
          <thead>
            <tr className="border-b border-white/5 bg-slate-900/80">
              <th className="p-4 font-semibold text-slate-400 sticky left-0 bg-slate-900 z-10 w-[220px]">
                Metric
              </th>
              {comparison.entries.map((entry) => {
                const isClearWinner = comparison.is_clear_winner && entry.solution_title === clearWinnerTitle;
                const isApproved = approvedSolutionId === entry.solution_id;

                return (
                  <th
                    key={entry.solution_title}
                    className={`p-6 font-bold text-white text-center border-l border-white/5 transition-all relative ${
                      isApproved
                        ? "bg-emerald-950/20 border-emerald-500/40"
                        : isClearWinner
                        ? "bg-emerald-950/10 border-emerald-500/20"
                        : ""
                    }`}
                  >
                    {isApproved && (
                      <div className="absolute top-2 right-2 px-2 py-0.5 bg-emerald-500 text-white rounded text-[10px] uppercase font-bold tracking-wider">
                        Approved ✓
                      </div>
                    )}
                    <span className="text-base block">{entry.solution_title}</span>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {/* Weighted Average */}
            <tr className="border-b border-white/5 hover:bg-slate-800/40">
              <td className="p-4 font-medium text-slate-300 sticky left-0 bg-slate-900 z-10 border-r border-white/5">
                Weighted Average Score
              </td>
              {comparison.entries.map((entry) => {
                const isLeader = scoreLeader === entry.solution_title;
                const isApproved = approvedSolutionId === entry.solution_id;
                const progressWidth = `${(entry.weighted_avg / 5.0) * 100}%`;

                return (
                  <td
                    key={entry.solution_title}
                    className={`p-6 text-center border-l border-white/5 transition-all ${
                      isApproved ? "bg-emerald-950/10" : ""
                    }`}
                  >
                    <div className="space-y-2 flex flex-col items-center">
                      <div className="flex items-center gap-1.5 justify-center">
                        <span className={`text-lg font-extrabold ${isLeader ? "text-amber-400" : "text-white"}`}>
                          {entry.weighted_avg.toFixed(2)}
                        </span>
                        {isLeader && <MetricLeaderBadge />}
                      </div>
                      <div className="w-24 h-1.5 bg-slate-950 rounded-full overflow-hidden border border-white/5">
                        <div
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: progressWidth }}
                        />
                      </div>
                    </div>
                  </td>
                );
              })}
            </tr>

            {/* Minimum Score */}
            <tr className="border-b border-white/5 hover:bg-slate-800/40">
              <td className="p-4 font-medium text-slate-300 sticky left-0 bg-slate-900 z-10 border-r border-white/5">
                Minimum Score
              </td>
              {comparison.entries.map((entry) => {
                const isLeader = minScoreLeader === entry.solution_title;
                const isApproved = approvedSolutionId === entry.solution_id;
                const isCritical = entry.min_score <= 2;

                return (
                  <td
                    key={entry.solution_title}
                    className={`p-6 text-center border-l border-white/5 transition-all ${
                      isApproved ? "bg-emerald-950/10" : ""
                    }`}
                  >
                    <div className="flex items-center gap-1.5 justify-center">
                      <span className={`text-lg font-extrabold ${
                        isCritical ? "text-red-400" : isLeader ? "text-amber-400" : "text-white"
                      }`}>
                        {entry.min_score}
                      </span>
                      {isLeader && <MetricLeaderBadge />}
                    </div>
                  </td>
                );
              })}
            </tr>

            {/* Devil's Advocate */}
            <tr className="border-b border-white/5 hover:bg-slate-800/40">
              <td className="p-4 font-medium text-slate-300 sticky left-0 bg-slate-900 z-10 border-r border-white/5">
                Devil's Advocate
              </td>
              {comparison.entries.map((entry) => {
                const isLeader = attackLeader === entry.solution_title;
                const isApproved = approvedSolutionId === entry.solution_id;
                const isExpanded = !!expandedAttacks[entry.solution_title];

                return (
                  <td
                    key={entry.solution_title}
                    className={`p-6 border-l border-white/5 transition-all max-w-[280px] ${
                      isApproved ? "bg-emerald-950/10" : ""
                    }`}
                  >
                    <div className="flex flex-col items-center gap-3">
                      <div className="flex items-center gap-1.5 justify-center">
                        <div className={`px-2.5 py-1 rounded-full border font-bold text-xs flex items-center gap-1 ${
                          entry.attack_survives
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : "bg-red-500/10 text-red-400 border-red-500/20"
                        }`}>
                          {entry.attack_survives ? (
                            <Check className="w-3.5 h-3.5" />
                          ) : (
                            <X className="w-3.5 h-3.5" />
                          )}
                          <span>{entry.attack_survives ? "Survives" : "Fails"}</span>
                        </div>
                        {isLeader && <MetricLeaderBadge />}
                      </div>

                      <p className={`text-xs text-slate-300 text-center leading-relaxed transition-all ${
                        isExpanded ? "" : "line-clamp-2"
                      }`}>
                        {entry.attack_summary}
                      </p>

                      <button
                        onClick={() => toggleExpand(entry.solution_title)}
                        className="text-[10px] text-blue-400 hover:text-blue-300 underline font-semibold focus:outline-none"
                      >
                        {isExpanded ? "Show less" : "Read full attack"}
                      </button>
                    </div>
                  </td>
                );
              })}
            </tr>

            {/* Inconsistencies */}
            <tr className="hover:bg-slate-800/40">
              <td className="p-4 font-medium text-slate-300 sticky left-0 bg-slate-900 z-10 border-r border-white/5">
                Evidence Inconsistencies
              </td>
              {comparison.entries.map((entry) => {
                const isLeader = inconsistencyLeader === entry.solution_title;
                const isApproved = approvedSolutionId === entry.solution_id;
                const percent = (entry.inconsistency_count / maxInconsistencies) * 100;

                return (
                  <td
                    key={entry.solution_title}
                    className={`p-6 text-center border-l border-white/5 transition-all ${
                      isApproved ? "bg-emerald-950/10" : ""
                    }`}
                  >
                    <div className="space-y-2 flex flex-col items-center">
                      <div className="flex items-center gap-1.5 justify-center">
                        <span className={`text-lg font-extrabold ${isLeader ? "text-amber-400" : "text-white"}`}>
                          {entry.inconsistency_count}
                        </span>
                        {isLeader && <MetricLeaderBadge />}
                      </div>
                      <div className="w-24 h-1.5 bg-slate-950 rounded-full overflow-hidden border border-white/5">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            entry.inconsistency_count === 0
                              ? "bg-emerald-500"
                              : entry.inconsistency_count <= 2
                              ? "bg-amber-500"
                              : "bg-red-500"
                          }`}
                          style={{ width: `${percent}%` }}
                        />
                      </div>
                    </div>
                  </td>
                );
              })}
            </tr>
          </tbody>
        </table>
      </div>

      {/* Decision Section */}
      <div className="pt-8 border-t border-white/5 space-y-6">
        <div className="space-y-1">
          <h4 className="font-bold text-white text-base">Make Final Decision</h4>
          <p className="text-sm text-slate-400">
            The system does not make this decision. Review the analysis above and select the solution you want to move forward with.
          </p>
        </div>

        {approvedSolutionId ? (
          <div className="bg-emerald-950/20 border border-emerald-500/20 rounded-2xl p-6 flex flex-col md:flex-row items-center justify-between gap-4 shadow-lg animate-in fade-in slide-in-from-bottom-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20">
                <Check className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-white">Solution Selected</p>
                <p className="text-xs text-slate-400">You approved this solution for development.</p>
              </div>
            </div>
            <Link
              to="/approvals"
              className="w-full md:w-auto px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold rounded-xl shadow-lg transition-all flex items-center justify-center gap-1.5"
            >
              <span>View in Approvals Queue</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        ) : (
          <div className="flex flex-col md:flex-row items-stretch md:items-center gap-4 justify-between">
            <div className="flex flex-wrap gap-3">
              {comparison.entries.map((entry) => (
                <button
                  key={entry.solution_id}
                  onClick={() => handleApprove(entry.solution_id)}
                  className="px-6 py-2.5 border border-blue-600 hover:bg-blue-600 text-blue-400 hover:text-white font-semibold rounded-xl transition-all text-sm flex items-center gap-1.5"
                >
                  <span>Approve {entry.solution_title}</span>
                </button>
              ))}
            </div>

            {onRegenerateSolutions && (
              <button
                onClick={onRegenerateSolutions}
                className="text-slate-400 hover:text-red-400 text-sm font-semibold transition-colors underline focus:outline-none"
              >
                None — Regenerate Solutions
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ComparisonMatrix;
