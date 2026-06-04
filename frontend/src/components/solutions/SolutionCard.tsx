import React from "react";
import { Users, DollarSign } from "lucide-react";
import { type Solution } from "../../types/api";
import { useSolutionStore } from "../../stores/solutionStore";
import TechStackEditor from "./TechStackEditor";
import { CompetitorAnalysis } from "./CompetitorAnalysis";

interface SolutionCardProps {
  solution: Solution;
}

const SolutionCard: React.FC<SolutionCardProps> = ({ solution }) => {
  const { updateSolution } = useSolutionStore();
  
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

  const statusColor = getStatusColor(solution.status);

  return (
    <div className="bg-slate-800/50 border border-white/5 rounded-2xl p-6 hover:border-white/20 transition-all duration-300 shadow-xl backdrop-blur-sm">
      {/* Header Row */}
      <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-white">{solution.title}</h3>
          {solution.is_unconventional && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-500 border border-amber-500/20">
              ⚡ Unconventional
            </span>
          )}
        </div>
        
        {/* Status Indicator */}
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${statusColor.dot}`} />
          <span className={`text-xs font-medium capitalize ${statusColor.text}`}>
            {solution.status}
          </span>
        </div>
      </div>

      {/* Description */}
      <p className="text-slate-300 mb-6 leading-relaxed">
        {solution.description}
      </p>

      {/* Mechanism Section */}
      {solution.mechanism && (
        <div className="mb-6">
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            How it works
          </h4>
          <div className="bg-slate-900/50 rounded-xl p-4 border-l-2 border-blue-500 text-slate-300 text-sm leading-relaxed">
            {solution.mechanism}
          </div>
        </div>
      )}

      {/* Tech Stack Section */}
      <div className="mb-6">
        <TechStackEditor
          techStack={solution.tech_stack || []}
          onSave={async (updatedTechStack) => {
            await updateSolution(solution.id, { tech_stack: updatedTechStack });
          }}
        />
      </div>

      {/* Bottom Row */}
      <div className="flex flex-wrap items-center gap-6 pt-4 border-t border-white/5 text-sm text-slate-400">
        {solution.target_user && (
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-slate-500" />
            <span>{solution.target_user}</span>
          </div>
        )}
        {solution.revenue_model && (
          <div className="flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-slate-500" />
            <span>{solution.revenue_model}</span>
          </div>
        )}
      </div>

      {/* Competitor Analysis */}
      <CompetitorAnalysis solutionId={solution.id} />
    </div>
  );
};

export default SolutionCard;
