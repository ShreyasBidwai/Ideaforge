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
  Sparkles,
  ArrowLeft
} from "lucide-react";
import apiClient from "../services/api";
import { useToastStore } from "../stores/toastStore";
import ErrorBoundary from "../components/ui/ErrorBoundary";
import ErrorDisplay from "../components/ui/ErrorDisplay";
import LoadingSpinner from "../components/ui/LoadingSpinner";
import EmptyState from "../components/ui/EmptyState";

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
  const [projectsMap, setProjectsMap] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isBuildingId, setIsBuildingId] = useState<string | null>(null);

  // Tech Stack Modal Configuration States
  const [activeSolutionForModal, setActiveSolutionForModal] = useState<ApprovedSolution | null>(null);
  const [projectType, setProjectType] = useState<"backend_only" | "fullstack">("fullstack");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [recommendationExplanation, setRecommendationExplanation] = useState<string>("");
  const [isRecommending, setIsRecommending] = useState(false);
  const [newTagInput, setNewTagInput] = useState("");

  const fetchApprovals = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [appResponse, projResponse] = await Promise.all([
        apiClient.get<ApprovedSolution[]>("/api/v1/approvals"),
        apiClient.get("/api/v1/projects")
      ]);
      setApprovals(appResponse.data || []);
      
      const map: Record<string, string> = {};
      if (Array.isArray(projResponse.data)) {
        projResponse.data.forEach((p: any) => {
          map[p.solution_id] = p.id;
        });
      }
      setProjectsMap(map);
    } catch (err) {
      console.error("Failed to load approved solutions:", err);
      setError("Failed to load approved solutions. Please check your connection and try again.");
      addToast("error", "Failed to fetch approved solutions");
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenConfigModal = async (sol: ApprovedSolution) => {
    setActiveSolutionForModal(sol);
    setProjectType("fullstack");
    setRecommendationExplanation("");
    setSelectedTags(sol.tech_stack || []);
    setIsRecommending(true);
    
    try {
      const res = await apiClient.get(`/api/v1/solutions/${sol.id}/recommend-tech-stack?project_type=fullstack`);
      setSelectedTags(res.data.recommended_stack || []);
      setRecommendationExplanation(res.data.explanation || "");
    } catch (err) {
      console.error("Failed to load tech stack recommendations:", err);
      addToast("error", "Failed to load AI recommendations. Falling back to default.");
    } finally {
      setIsRecommending(false);
    }
  };

  const handleProjectTypeChange = async (type: "backend_only" | "fullstack") => {
    if (!activeSolutionForModal) return;
    setProjectType(type);
    setIsRecommending(true);
    try {
      const res = await apiClient.get(`/api/v1/solutions/${activeSolutionForModal.id}/recommend-tech-stack?project_type=${type}`);
      setSelectedTags(res.data.recommended_stack || []);
      setRecommendationExplanation(res.data.explanation || "");
    } catch (err) {
      console.error("Failed to load tech stack recommendations:", err);
      addToast("error", "Failed to load AI recommendations.");
    } finally {
      setIsRecommending(false);
    }
  };

  const handleBuildApp = async () => {
    if (!activeSolutionForModal) return;
    setIsBuildingId(activeSolutionForModal.id);
    try {
      const res = await apiClient.post(`/api/v1/solutions/${activeSolutionForModal.id}/create-project`, {
        tech_stack: selectedTags
      });
      addToast("success", "Project created successfully");
      setActiveSolutionForModal(null);
      navigate(`/projects/${res.data.id}`);
    } catch (err) {
      console.error("Failed to create project:", err);
      addToast("error", "Failed to create project");
    } finally {
      setIsBuildingId(null);
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

  if (error) {
    return (
      <ErrorBoundary>
        <ErrorDisplay
          title="Approvals Error"
          message={error}
          onRetry={fetchApprovals}
          showHome
        />
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <div className="w-full max-w-5xl mx-auto px-4 py-8 space-y-8 text-white">
        {/* Back to Dashboard */}
        <div>
          <button
            onClick={() => navigate("/")}
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Dashboard</span>
          </button>
        </div>

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
              {isLoading ? <LoadingSpinner size="sm" variant="inline" /> : approvals.length} Approved
            </span>
          </div>
        </div>

        {/* Main content list */}
        {isLoading ? (
          <LoadingSpinner message="Loading approved solutions..." />
        ) : approvals.length === 0 ? (
          <EmptyState
            icon={CheckCircle}
            title="No approved solutions yet"
            message="Complete an evaluation and approve a solution to see it here"
            actionLabel="Start Discovery"
            onAction={() => navigate("/discovery")}
          />
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

                  {projectsMap[sol.id] ? (
                    <button
                      onClick={() => navigate(`/projects/${projectsMap[sol.id]}`)}
                      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold border border-indigo-500/20 transition-all flex items-center gap-1.5"
                    >
                      <span>View Project</span>
                    </button>
                  ) : (
                    <button
                      onClick={() => handleOpenConfigModal(sol)}
                      disabled={isBuildingId !== null}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold border border-blue-500/10 transition-all flex items-center gap-1.5"
                    >
                      <span>Build App</span>
                    </button>
                  )}

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

      <AnimatePresence>
        {activeSolutionForModal && (
          <div className="fixed inset-0 z-50 overflow-y-auto flex items-start justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className="bg-slate-900 border border-white/10 rounded-2xl w-full max-w-lg p-6 shadow-2xl relative text-white my-auto space-y-6"
            >
              {/* Title */}
              <div className="space-y-1.5 border-b border-white/5 pb-4">
                <h3 className="text-lg font-bold flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-indigo-400" />
                  Configure Tech Stack
                </h3>
                <p className="text-slate-400 text-xs leading-normal">
                  Customize the languages, databases, and frameworks for <span className="text-white font-medium">{activeSolutionForModal.title}</span>.
                </p>
              </div>

              {/* Project Type Selector */}
              <div className="space-y-2">
                <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Project Target Architecture
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => handleProjectTypeChange("backend_only")}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      projectType === "backend_only"
                        ? "bg-indigo-600/10 border-indigo-500 text-white"
                        : "bg-slate-950/40 border-white/5 text-slate-400 hover:border-white/10 hover:text-white"
                    }`}
                  >
                    <div className="text-xs font-bold mb-0.5">Backend Only</div>
                    <div className="text-[10px] opacity-70 leading-normal">Clean APIs, background processes & databases.</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleProjectTypeChange("fullstack")}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      projectType === "fullstack"
                        ? "bg-indigo-600/10 border-indigo-500 text-white"
                        : "bg-slate-950/40 border-white/5 text-slate-400 hover:border-white/10 hover:text-white"
                    }`}
                  >
                    <div className="text-xs font-bold mb-0.5">Fullstack App</div>
                    <div className="text-[10px] opacity-70 leading-normal">Includes React client dashboard & layouts.</div>
                  </button>
                </div>
              </div>

              {/* AI Rationale */}
              <div className="space-y-2">
                <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                  AI Rationale & Strategy
                </label>
                <div className="bg-slate-950/40 border border-white/5 rounded-xl p-3 min-h-[80px] flex items-center justify-center">
                  {isRecommending ? (
                    <div className="flex flex-col items-center gap-2 text-xs text-slate-400">
                      <LoadingSpinner size="sm" variant="inline" />
                      <span>Fetching recommendations...</span>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-300 leading-relaxed w-full">
                      {recommendationExplanation || "No explanation provided."}
                    </p>
                  )}
                </div>
              </div>

              {/* Selected Tech Tags */}
              <div className="space-y-2">
                <label className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Finalized Tech Stack Tags
                </label>
                <div className="flex flex-wrap gap-2 max-h-[100px] overflow-y-auto bg-slate-950/30 p-2.5 border border-white/5 rounded-xl">
                  {selectedTags.map((tag) => (
                    <span
                      key={tag}
                      className="bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-[10px] font-bold px-2 py-0.5 rounded-md flex items-center gap-1.5"
                    >
                      <span>{tag}</span>
                      <button
                        type="button"
                        onClick={() => setSelectedTags((prev) => prev.filter((t) => t !== tag))}
                        className="hover:text-white font-black text-xs text-indigo-400/70"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                  {selectedTags.length === 0 && (
                    <span className="text-[10px] text-slate-500 italic">No technologies selected yet.</span>
                  )}
                </div>
              </div>

              {/* Add Custom Tag */}
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={newTagInput}
                  onChange={(e) => setNewTagInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && newTagInput.trim()) {
                      e.preventDefault();
                      if (!selectedTags.includes(newTagInput.trim())) {
                        setSelectedTags((prev) => [...prev, newTagInput.trim()]);
                      }
                      setNewTagInput("");
                    }
                  }}
                  placeholder="Add custom technology (e.g. Redis, Docker)..."
                  className="bg-slate-950/40 border border-white/5 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-white/20 flex-1"
                />
                <button
                  type="button"
                  onClick={() => {
                    if (newTagInput.trim()) {
                      if (!selectedTags.includes(newTagInput.trim())) {
                        setSelectedTags((prev) => [...prev, newTagInput.trim()]);
                      }
                      setNewTagInput("");
                    }
                  }}
                  className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-white border border-white/5 rounded-xl text-xs font-semibold"
                >
                  Add
                </button>
              </div>

              {/* Footer Buttons */}
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/5">
                <button
                  type="button"
                  onClick={() => setActiveSolutionForModal(null)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-semibold border border-white/5 transition-all"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleBuildApp}
                  disabled={isBuildingId !== null || selectedTags.length === 0}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold border border-blue-500/10 transition-all flex items-center gap-1.5"
                >
                  {isBuildingId ? <LoadingSpinner size="sm" variant="inline" /> : "Confirm & Create"}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
      </div>
    </ErrorBoundary>
  );
};

export default Approvals;
