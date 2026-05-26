import React, { useState } from "react";
import { type Solution } from "../../types/api";

interface SolutionComparisonProps {
  solutions: Solution[];
}

const ExpandableCell: React.FC<{ text: string; limit?: number }> = ({ text, limit = 100 }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  if (!text) return <span className="text-slate-500">—</span>;
  if (text.length <= limit) return <span>{text}</span>;

  return (
    <div>
      <span className="whitespace-pre-line">{isExpanded ? text : `${text.substring(0, limit)}...`}</span>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="text-blue-400 hover:text-blue-300 text-xs font-semibold ml-2 focus:outline-none focus:underline"
      >
        {isExpanded ? "Show less" : "Read more"}
      </button>
    </div>
  );
};

const SolutionComparison: React.FC<SolutionComparisonProps> = ({ solutions }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "candidate":
        return { dot: "bg-blue-500", text: "text-blue-400" };
      case "disqualified":
        return { dot: "bg-red-500", text: "text-red-400" };
      case "evaluated":
        return { dot: "bg-green-500", text: "text-green-400" };
      case "approved":
        return { dot: "bg-emerald-500", text: "text-emerald-400" };
      default:
        return { dot: "bg-slate-500", text: "text-slate-400" };
    }
  };

  return (
    <div className="overflow-x-auto w-full border border-white/5 rounded-2xl bg-slate-900/30 backdrop-blur-sm shadow-xl">
      <table className="min-w-full border-collapse text-left">
        <thead>
          <tr className="border-b border-white/5">
            <th className="p-4 text-xs font-semibold uppercase tracking-wider text-slate-400 bg-slate-900/50 w-48 sticky left-0 z-10 backdrop-blur border-r border-white/5">
              Dimension
            </th>
            {solutions.map((sol, index) => {
              const bgClass = index % 2 === 0 ? "bg-slate-800/30" : "bg-slate-900/20";
              const borderClass = sol.is_unconventional ? "border-l-2 border-l-amber-500/40" : "";
              return (
                <th
                  key={sol.id}
                  className={`p-4 text-base font-bold text-white min-w-[280px] align-top ${bgClass} ${borderClass}`}
                >
                  <span>{sol.title}</span>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5 text-sm text-slate-300">
          {/* Description */}
          <tr>
            <td className="p-4 font-semibold text-slate-400 bg-slate-900/50 sticky left-0 z-10 backdrop-blur border-r border-white/5">
              Description
            </td>
            {solutions.map((sol, index) => {
              const bgClass = index % 2 === 0 ? "bg-slate-800/10" : "bg-slate-900/5";
              const borderClass = sol.is_unconventional ? "border-l-2 border-l-amber-500/40" : "";
              return (
                <td key={sol.id} className={`p-4 align-top leading-relaxed ${bgClass} ${borderClass}`}>
                  <ExpandableCell text={sol.description} />
                </td>
              );
            })}
          </tr>

          {/* Mechanism */}
          <tr>
            <td className="p-4 font-semibold text-slate-400 bg-slate-900/50 sticky left-0 z-10 backdrop-blur border-r border-white/5">
              How it works
            </td>
            {solutions.map((sol, index) => {
              const bgClass = index % 2 === 0 ? "bg-slate-800/10" : "bg-slate-900/5";
              const borderClass = sol.is_unconventional ? "border-l-2 border-l-amber-500/40" : "";
              return (
                <td key={sol.id} className={`p-4 align-top leading-relaxed ${bgClass} ${borderClass}`}>
                  <ExpandableCell text={sol.mechanism || ""} />
                </td>
              );
            })}
          </tr>

          {/* Tech Stack */}
          <tr>
            <td className="p-4 font-semibold text-slate-400 bg-slate-900/50 sticky left-0 z-10 backdrop-blur border-r border-white/5">
              Tech Stack
            </td>
            {solutions.map((sol, index) => {
              const bgClass = index % 2 === 0 ? "bg-slate-800/10" : "bg-slate-900/5";
              const borderClass = sol.is_unconventional ? "border-l-2 border-l-amber-500/40" : "";
              return (
                <td key={sol.id} className={`p-4 align-top ${bgClass} ${borderClass}`}>
                  <div className="flex flex-wrap gap-1.5">
                    {sol.tech_stack?.map((tech, idx) => (
                      <span
                        key={idx}
                        className="bg-slate-700/40 text-slate-300 text-xs px-2.5 py-0.5 rounded border border-white/5"
                      >
                        {tech}
                      </span>
                    )) || <span className="text-slate-500">—</span>}
                  </div>
                </td>
              );
            })}
          </tr>

          {/* Target User */}
          <tr>
            <td className="p-4 font-semibold text-slate-400 bg-slate-900/50 sticky left-0 z-10 backdrop-blur border-r border-white/5">
              Target User
            </td>
            {solutions.map((sol, index) => {
              const bgClass = index % 2 === 0 ? "bg-slate-800/10" : "bg-slate-900/5";
              const borderClass = sol.is_unconventional ? "border-l-2 border-l-amber-500/40" : "";
              return (
                <td key={sol.id} className={`p-4 align-top ${bgClass} ${borderClass}`}>
                  {sol.target_user || <span className="text-slate-500">—</span>}
                </td>
              );
            })}
          </tr>

          {/* Revenue Model */}
          <tr>
            <td className="p-4 font-semibold text-slate-400 bg-slate-900/50 sticky left-0 z-10 backdrop-blur border-r border-white/5">
              Revenue Model
            </td>
            {solutions.map((sol, index) => {
              const bgClass = index % 2 === 0 ? "bg-slate-800/10" : "bg-slate-900/5";
              const borderClass = sol.is_unconventional ? "border-l-2 border-l-amber-500/40" : "";
              return (
                <td key={sol.id} className={`p-4 align-top ${bgClass} ${borderClass}`}>
                  {sol.revenue_model || <span className="text-slate-500">—</span>}
                </td>
              );
            })}
          </tr>

          {/* Type */}
          <tr>
            <td className="p-4 font-semibold text-slate-400 bg-slate-900/50 sticky left-0 z-10 backdrop-blur border-r border-white/5">
              Type
            </td>
            {solutions.map((sol, index) => {
              const bgClass = index % 2 === 0 ? "bg-slate-800/10" : "bg-slate-900/5";
              const borderClass = sol.is_unconventional ? "border-l-2 border-l-amber-500/40" : "";
              return (
                <td key={sol.id} className={`p-4 align-top ${bgClass} ${borderClass}`}>
                  {sol.is_unconventional ? (
                    <span className="text-amber-500 font-medium">⚡ Unconventional</span>
                  ) : (
                    <span className="text-slate-400">Conventional</span>
                  )}
                </td>
              );
            })}
          </tr>

          {/* Status */}
          <tr>
            <td className="p-4 font-semibold text-slate-400 bg-slate-900/50 sticky left-0 z-10 backdrop-blur border-r border-white/5">
              Status
            </td>
            {solutions.map((sol, index) => {
              const bgClass = index % 2 === 0 ? "bg-slate-800/10" : "bg-slate-900/5";
              const borderClass = sol.is_unconventional ? "border-l-2 border-l-amber-500/40" : "";
              const colors = getStatusColor(sol.status);
              return (
                <td key={sol.id} className={`p-4 align-top ${bgClass} ${borderClass}`}>
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${colors.dot}`} />
                    <span className={`text-xs font-semibold capitalize ${colors.text}`}>{sol.status}</span>
                  </div>
                </td>
              );
            })}
          </tr>
        </tbody>
      </table>
    </div>
  );
};

export default SolutionComparison;
