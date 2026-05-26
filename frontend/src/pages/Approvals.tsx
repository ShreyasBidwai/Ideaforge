import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle,
  Users,
  DollarSign,
  TrendingUp,
  ShieldAlert,
  ArrowRight,
  Sparkles
} from "lucide-react";
import apiClient from "../services/api";
import { useToastStore } from "../stores/toastStore";

interface ApprovedSolution {
  id: string;
  problem_id: string;
  title: string;
  description: string;
  mechanism: string | null;
  tech_stack: string[] | null;
  target_user: string | null;
  revenue_model: string | null;
  is_unconventional: boolean;
  status: string;
  created_at: string;
  updated_at: string;
  
  // Context & Metrics
  problem_title: string;
  industry: string;
  location: string;
  weighted_avg: number | null;
  min_score: number | null;
  attack_survives: boolean | null;
  inconsistency_count: number | null;
}

const Approvals: React.FC = () => {
  const navigate = useNavigate();
  const { addToast } = useToastStore();
  const [approvals, setApprovals] = useState<ApprovedSolution[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchApprovals = async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.get<ApprovedSolution[]>("/api/v1/approvals");
      setApprovals(response.data || []);
    } catch (err) {
      console.error("Failed to load approved solutions:", err);
      addToast("error", "Failed to fetch approved solutions");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
  }, []);

  const handleRevoke = async (id: string) => {
    try {
      await apiClient.post(`/api/v1/solutions/${id}/revoke`);
      addToast("success", "Approval revoked successfully");
      // Remove it locally or trigger a reload
      setApprovals((prev) => prev.filter((app) => app.id !== id));
    } catch (err) {
      console.error("Failed to revoke approval:", err);
      addToast("error", "Failed to revoke approval");
    }
  };

  const formatApprovalDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(undefined, {
      year: "numeric",
      month: "long",
      day: "numeric"
    });
  };

  return (
    <div className="w-full max-w-5xl mx-auto px-4 py-8 space-y-8 text-white">
      {/* Header section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/5 pb-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <CheckCircle className="text-emerald-500 w-7 h-7" />
            <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              Approved Solutions
            </h1>
          </div>
          <p className="text-slate-400 text-sm">
            Solutions approved for Phase 2 — architecture docs, PRDs, and technical specifications
          </p>
        </div>

        <div>
          <span className="bg-emerald-500/15 text-emerald-400 border border-emerald-500/25 text-xs font-bold px-4 py-2 rounded-full uppercase tracking-wider">
            {isLoading ? "..." : approvals.length} Approved
          </span>
        </div>
      </div>

      {/* Main content list */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20 text-slate-500">
          Loading approved solutions...
        </div>
      ) : approvals.length === 0 ? (
        /* Empty State */
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center justify-center text-center py-16 px-4 bg-slate-900/40 border border-white/5 rounded-3xl shadow-xl space-y-5"
        >
          <div className="w-16 h-16 bg-slate-800/80 rounded-2xl flex items-center justify-center border border-white/5 text-slate-500">
            <CheckCircle size={32} />
          </div>
          <div className="space-y-2 max-w-md">
            <h3 className="text-lg font-bold text-white">No approved solutions yet</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Complete an evaluation and approve a solution to see it here
            </p>
          </div>
          <button
            onClick={() => navigate("/discovery")}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl text-sm shadow-lg shadow-blue-600/20 hover:shadow-blue-500/30 transition-all flex items-center gap-2 hover:-translate-y-0.5 active:translate-y-0"
          >
            <span>Start Discovery</span>
            <ArrowRight size={16} />
          </button>
        </motion.div>
      ) : (
        /* Vertical Cards Stack */
        <div className="flex flex-col gap-6">
          <AnimatePresence mode="popLayout">
            {approvals.map((sol, index) => (
              <motion.div
                key={sol.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                className="bg-slate-900/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6 shadow-xl relative overflow-hidden flex flex-col"
              >
                {/* Top Row */}
                <div className="flex flex-wrap items-start justify-between gap-4 mb-3">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-bold text-white">{sol.title}</h3>
                    {sol.is_unconventional && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20 uppercase tracking-wider">
                        ⚡ Unconventional
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2.5 text-xs">
                    <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-1 rounded-full font-bold uppercase tracking-wider">
                      Approved ✓
                    </span>
                    <span className="text-slate-500">
                      {formatApprovalDate(sol.updated_at)}
                    </span>
                  </div>
                </div>

                {/* Context Row */}
                <div className="flex flex-wrap items-center gap-2 mb-4 text-xs">
                  <span className="text-slate-400 font-medium">{sol.problem_title}</span>
                  <span className="text-slate-600">→</span>
                  <span className="bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full font-medium">
                    {sol.industry}
                  </span>
                  <span className="bg-slate-850 text-slate-300 border border-white/5 px-2 py-0.5 rounded-full font-medium">
                    {sol.location}
                  </span>
                </div>

                {/* Description */}
                <p className="text-slate-300 text-sm mb-5 leading-relaxed">
                  {sol.description}
                </p>

                {/* Mechanism styled block */}
                {sol.mechanism && (
                  <div className="mb-5">
                    <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                      How it works
                    </div>
                    <div className="bg-slate-950/50 rounded-xl p-4 border-l-2 border-blue-500 text-slate-300 text-xs sm:text-sm leading-relaxed">
                      {sol.mechanism}
                    </div>
                  </div>
                )}

                {/* Tech Stack tags */}
                {sol.tech_stack && sol.tech_stack.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-5">
                    {sol.tech_stack.map((tech) => (
                      <span
                        key={tech}
                        className="bg-slate-800 text-slate-300 text-[10px] font-semibold px-2.5 py-1 rounded-md border border-white/5"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                )}

                {/* Evaluation Summary metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-slate-950/40 border border-white/5 rounded-xl p-4 mb-5 text-xs text-slate-400">
                  <div className="flex flex-col gap-0.5">
                    <span className="text-[9px] font-semibold text-slate-500 uppercase tracking-wider">Weighted Avg</span>
                    <span className="text-white font-bold text-sm">
                      {sol.weighted_avg !== null ? sol.weighted_avg.toFixed(2) : "N/A"}
                    </span>
                  </div>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-[9px] font-semibold text-slate-500 uppercase tracking-wider">Min Score</span>
                    <span className={`text-sm font-bold ${sol.min_score !== null && sol.min_score <= 2 ? "text-rose-400" : "text-white"}`}>
                      {sol.min_score !== null ? sol.min_score : "N/A"}
                    </span>
                  </div>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-[9px] font-semibold text-slate-500 uppercase tracking-wider">Attack Survival</span>
                    {sol.attack_survives !== null ? (
                      <span className={`text-sm font-bold ${sol.attack_survives ? "text-emerald-400" : "text-rose-400"}`}>
                        {sol.attack_survives ? "✓ Survives" : "✗ Fails"}
                      </span>
                    ) : (
                      <span className="text-slate-400 text-sm font-bold">N/A</span>
                    )}
                  </div>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-[9px] font-semibold text-slate-500 uppercase tracking-wider">Inconsistencies</span>
                    <span className="text-white text-sm font-bold">
                      {sol.inconsistency_count !== null ? sol.inconsistency_count : 0}
                    </span>
                  </div>
                </div>

                {/* Bottom metadata row */}
                <div className="flex flex-wrap items-center gap-6 pb-4 mb-5 border-b border-white/5 text-xs text-slate-400">
                  {sol.target_user && (
                    <div className="flex items-center gap-1.5">
                      <Users size={14} className="text-slate-500" />
                      <span>{sol.target_user}</span>
                    </div>
                  )}
                  {sol.revenue_model && (
                    <div className="flex items-center gap-1.5">
                      <DollarSign size={14} className="text-slate-500" />
                      <span>{sol.revenue_model}</span>
                    </div>
                  )}
                </div>

                {/* Actions row */}
                <div className="flex flex-wrap items-center gap-3">
                  <button
                    onClick={() => navigate(`/evaluation/${sol.problem_id}`)}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-semibold border border-white/5 transition-all"
                  >
                    View Full Evaluation
                  </button>

                  <button
                    disabled
                    title="Coming in Phase 2"
                    className="px-4 py-2 bg-blue-600/20 text-blue-400/50 cursor-not-allowed rounded-xl text-xs font-semibold border border-blue-500/10 transition-all flex items-center gap-1.5"
                  >
                    <span>Generate Documents</span>
                  </button>

                  <button
                    onClick={() => handleRevoke(sol.id)}
                    className="px-4 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 rounded-xl text-xs font-semibold border border-rose-500/20 transition-all ml-auto"
                  >
                    Revoke Approval
                  </button>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
};

export default Approvals;
