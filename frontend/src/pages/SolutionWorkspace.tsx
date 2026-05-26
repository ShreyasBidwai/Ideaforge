import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Play, Award } from "lucide-react";

import { useSolutionStore } from "../stores/solutionStore";
import { useToastStore } from "../stores/toastStore";
import { sessionService } from "../services/sessionService";
import SolutionCard from "../components/solutions/SolutionCard";
import SolutionSkeleton from "../components/solutions/SolutionSkeleton";
import GenerateSolutionsCTA from "../components/solutions/GenerateSolutionsCTA";
import ViewToggle from "../components/solutions/ViewToggle";
import SolutionComparison from "../components/solutions/SolutionComparison";
import { type Session } from "../types/api";

const SolutionWorkspace: React.FC = () => {
  const { problemId } = useParams<{ problemId: string }>();
  const navigate = useNavigate();
  const {
    solutions,
    currentProblem,
    isGenerating,
    isLoading,
    error,
    currentStep,
    progressMessage,
    fetchSolutions,
    generateSolutions,
    clearSolutions
  } = useSolutionStore();

  const { addToast } = useToastStore();
  const [session, setSession] = useState<Session | null>(null);
  const [view, setView] = useState<"cards" | "compare">("cards");

  useEffect(() => {
    if (problemId) {
      fetchSolutions(problemId);
    }
    return () => {
      clearSolutions();
    };
  }, [problemId, fetchSolutions, clearSolutions]);

  useEffect(() => {
    if (currentProblem) {
      sessionService.getSession(currentProblem.session_id)
        .then((res) => setSession(res))
        .catch((err) => console.error("Failed to load session info", err));
    }
  }, [currentProblem]);

  const handleGenerate = async () => {
    if (!problemId) return;
    try {
      addToast("info", "Generating technology solution candidates...");
      await generateSolutions(problemId);
      addToast("success", "Solution candidates generated successfully!");
      // Re-fetch to get up-to-date session/problem state
      fetchSolutions(problemId);
    } catch (err: any) {
      addToast("error", err.message || "Failed to generate solution candidates");
    }
  };

  const handleRunEvaluation = () => {
    if (problemId) {
      navigate(`/evaluation/${problemId}`);
    }
  };

  const getEvaluationStepsText = (level?: string) => {
    switch (level) {
      case "poc":
        return "This will run: Rubric Scoring";
      case "mvp":
        return "This will run: Rubric Scoring → Devil's Advocate";
      case "pre_production":
        return "This will run: Rubric Scoring → Devil's Advocate → ACH Analysis → Consistency Check → Rating Aggregation";
      case "production":
        return "This will run: Rubric Scoring → Devil's Advocate → ACH Analysis → Consistency Check → Rating Aggregation → Security Check → Compliance Check";
      default:
        return "This will run: Rubric → Scoring → Devil's Advocate → ACH Analysis";
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100 } }
  };

  const solutionsCount = solutions.length;
  const targetSolutionCount = session ? session.maturity_level === "poc" ? 3 : session.maturity_level === "mvp" ? 4 : 5 : 4;

  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans selection:bg-blue-600/30 selection:text-blue-200">
      {/* Top Section — Sticky Problem Context Bar */}
      <div className="sticky top-0 z-10 bg-slate-900/80 backdrop-blur border-b border-white/5 py-4 mb-6 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <Link
              to="/library"
              className="p-2 hover:bg-slate-800 rounded-xl transition-colors text-slate-400 hover:text-white"
              title="Back to Problem Library"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            {isLoading ? (
              <div className="h-6 w-48 bg-slate-800 rounded animate-pulse" />
            ) : (
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-lg font-bold text-white max-w-md truncate">
                    {currentProblem?.title || "Solution Workspace"}
                  </h1>
                  {currentProblem?.industry && (
                    <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-white/5">
                      {currentProblem.industry}
                    </span>
                  )}
                  {currentProblem?.location && (
                    <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-white/5">
                      {currentProblem.location}
                    </span>
                  )}
                  {session?.maturity_level && (
                    <span className="text-xs font-semibold bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded border border-blue-500/20 uppercase">
                      {session.maturity_level}
                    </span>
                  )}
                </div>
                {currentProblem?.overall_rating !== undefined && (
                  <div className="flex items-center gap-1.5 text-xs text-amber-400">
                    <Award className="w-3.5 h-3.5" />
                    <span>Rating: {currentProblem.overall_rating.toFixed(1)}/5.0</span>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            {solutionsCount > 0 && !isLoading && !isGenerating && (
              <ViewToggle view={view} onChange={setView} />
            )}
            <button
              onClick={handleRunEvaluation}
              disabled={solutionsCount === 0 || isLoading || isGenerating}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5 text-sm"
            >
              <Play className="w-4 h-4" />
              <span>Run Evaluation</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Section — Content Area */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 space-y-8">
        {isLoading || isGenerating ? (
          <div className="space-y-6">
            {isGenerating && (
              <div className="bg-slate-900/50 border border-white/5 rounded-2xl p-6 mb-6 backdrop-blur-sm max-w-xl mx-auto text-center space-y-4 shadow-xl">
                <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
                <div>
                  <p className="text-sm font-semibold text-white capitalize">
                    {currentStep ? `Status: ${currentStep}` : "Preparing..."}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    {progressMessage || "Analyzing session requirements..."}
                  </p>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-blue-600 h-1.5 rounded-full transition-all duration-500"
                    style={{
                      width:
                        currentStep === "preparing"
                          ? "25%"
                          : currentStep === "generating"
                          ? "50%"
                          : currentStep === "validating"
                          ? "75%"
                          : currentStep === "saving"
                          ? "90%"
                          : "10%"
                    }}
                  />
                </div>
              </div>
            )}
            <SolutionSkeleton />
          </div>
        ) : error ? (
          <div className="text-center p-8 bg-red-950/20 border border-red-500/20 rounded-2xl max-w-md mx-auto">
            <p className="text-red-400">{error}</p>
          </div>
        ) : solutionsCount === 0 ? (
          <GenerateSolutionsCTA
            onGenerate={handleGenerate}
            solutionCount={targetSolutionCount}
            isGenerating={isGenerating}
          />
        ) : (
          view === "compare" ? (
            <SolutionComparison solutions={solutions} />
          ) : (
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="show"
              className="space-y-6"
            >
              {solutions.map((solution) => (
                <motion.div key={solution.id} variants={cardVariants}>
                  <SolutionCard solution={solution} />
                </motion.div>
              ))}
            </motion.div>
          )
        )}

        {/* Bottom Section — Evaluation Run Bar */}
        {solutionsCount > 0 && !isLoading && !isGenerating && (
          <div className="border border-white/5 bg-slate-900/50 rounded-2xl p-6 shadow-xl backdrop-blur-sm space-y-4">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="space-y-1 text-center md:text-left">
                <h4 className="font-semibold text-white">Idea Evaluation Protocol</h4>
                <p className="text-sm text-slate-400">
                  {getEvaluationStepsText(session?.maturity_level)}
                </p>
              </div>
              
              <button
                onClick={handleRunEvaluation}
                disabled={solutionsCount < 2}
                className="w-full md:w-auto px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-blue-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Play className="w-5 h-5 fill-current" />
                <span>Run Evaluation Protocol</span>
              </button>
            </div>
            {solutionsCount < 2 && (
              <p className="text-xs text-red-400 text-center md:text-left">
                * At least 2 solution candidates are required to run the evaluation protocol.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SolutionWorkspace;
