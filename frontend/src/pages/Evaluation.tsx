import React, { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Check, Award, ShieldAlert } from "lucide-react";

import { useEvaluationStore } from "../stores/evaluationStore";
import { useToastStore } from "../stores/toastStore";
import RubricEditor from "../components/evaluation/RubricEditor";
import DisqualifierGate from "../components/evaluation/DisqualifierGate";
import ScoringTable from "../components/evaluation/ScoringTable";
import AttackCards from "../components/evaluation/AttackCards";
import ACHAnalysis from "../components/evaluation/ACHAnalysis";

const Evaluation: React.FC = () => {
  const { problemId } = useParams<{ problemId: string }>();
  const navigate = useNavigate();
  const { addToast } = useToastStore();

  const {
    currentStep,
    rubric,
    isRubricLocked,
    disqualifierResults,
    scores,
    attacks,
    achAnalysis,
    comparison,
    isLoading,
    maturitySteps,
    generateRubric,
    updateRubric,
    lockRubric,
    runDisqualifiers,
    runScoring,
    runAttacks,
    runACH,
    generateComparison: runGenerateComparison,
    loadFullEvaluation,
    setStep,
  } = useEvaluationStore();

  const [activeTab, setActiveTab] = useState<string>("rubric");

  useEffect(() => {
    if (problemId) {
      loadFullEvaluation(problemId);
    }
  }, [problemId, loadFullEvaluation]);

  useEffect(() => {
    setActiveTab(currentStep);
  }, [currentStep]);

  // Auto-run disqualifier check when entering disqualifiers step
  useEffect(() => {
    if (activeTab === "disqualifiers" && problemId && !disqualifierResults && !isLoading) {
      runDisqualifiers(problemId).catch((err) => {
        addToast("error", err.message || "Failed to run disqualifiers check");
      });
    }
  }, [activeTab, problemId, disqualifierResults, isLoading, runDisqualifiers, addToast]);

  // Auto-run scoring when entering scoring step
  useEffect(() => {
    if (activeTab === "scoring" && problemId && !scores && !isLoading) {
      runScoring(problemId).catch((err) => {
        addToast("error", err.message || "Failed to score solutions");
      });
    }
  }, [activeTab, problemId, scores, isLoading, runScoring, addToast]);

  // Auto-run attacks when entering attacks step
  useEffect(() => {
    if (activeTab === "attacks" && problemId && !attacks && !isLoading) {
      runAttacks(problemId).catch((err) => {
        addToast("error", err.message || "Failed to run Devil's Advocate attacks");
      });
    }
  }, [activeTab, problemId, attacks, isLoading, runAttacks, addToast]);

  // Auto-run ACH when entering ach step
  useEffect(() => {
    if (activeTab === "ach" && problemId && !achAnalysis && !isLoading) {
      runACH(problemId).catch((err) => {
        addToast("error", err.message || "Failed to run ACH Analysis");
      });
    }
  }, [activeTab, problemId, achAnalysis, isLoading, runACH, addToast]);

  // Auto-run comparison when entering comparison step
  useEffect(() => {
    if (activeTab === "comparison" && problemId && !comparison && !isLoading) {
      runGenerateComparison(problemId).catch((err) => {
        addToast("error", err.message || "Failed to generate Comparison Matrix");
      });
    }
  }, [activeTab, problemId, comparison, isLoading, runGenerateComparison, addToast]);

  const handleUpdateRubric = async (newRubric: any) => {
    if (!problemId) return;
    try {
      await updateRubric(problemId, newRubric);
    } catch (err: any) {
      addToast("error", err.message || "Failed to update rubric");
    }
  };

  const handleLockRubric = async () => {
    if (!problemId) return;
    try {
      await lockRubric(problemId);
      addToast("success", "Rubric locked successfully!");
      setStep("disqualifiers");
    } catch (err: any) {
      addToast("error", err.message || "Failed to lock rubric");
    }
  };

  const handleRegenerateRubric = async () => {
    if (!problemId) return;
    try {
      addToast("info", "Generating AI rubric...");
      await generateRubric(problemId);
      addToast("success", "Rubric generated successfully!");
    } catch (err: any) {
      addToast("error", err.message || "Failed to generate rubric");
    }
  };

  const handleContinueFromScoring = () => {
    if (maturitySteps.includes("attacks")) {
      setStep("attacks");
    } else {
      setStep("comparison");
    }
  };

  const handleContinueFromAttacks = () => {
    if (maturitySteps.includes("ach")) {
      setStep("ach");
    } else {
      setStep("comparison");
    }
  };

  const handleContinueFromACH = () => {
    setStep("comparison");
  };

  const stepDetails = [
    { id: "rubric", label: "Rubric" },
    { id: "disqualifiers", label: "Disqualifiers" },
    { id: "scoring", label: "Scoring" },
    { id: "attacks", label: "Attacks" },
    { id: "ach", label: "ACH" },
    { id: "comparison", label: "Comparison" },
  ];

  // Filter steps based on maturity requirements
  const stepsToShow = stepDetails.filter((step) => maturitySteps.includes(step.id));

  const getStepIndex = (stepId: string) => stepsToShow.findIndex((s) => s.id === stepId);
  const activeIndex = getStepIndex(activeTab);

  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans selection:bg-blue-600/30 selection:text-blue-200">
      {/* Top Header Section */}
      <div className="sticky top-0 z-10 bg-slate-900/80 backdrop-blur border-b border-white/5 py-4 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              to={problemId ? `/workspace/${problemId}` : "/library"}
              className="p-2 hover:bg-slate-800 rounded-xl transition-colors text-slate-400 hover:text-white"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="space-y-1">
              <h1 className="text-lg font-bold text-white flex items-center gap-2">
                <Award className="w-5 h-5 text-blue-500" />
                <span>Evaluation Protocol Wizard</span>
              </h1>
            </div>
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Progress Bar / Steps */}
        <div className="bg-slate-900 border border-white/5 rounded-2xl p-6 shadow-xl relative overflow-hidden">
          <div className="flex justify-between items-center relative z-10">
            {stepsToShow.map((step, idx) => {
              const isCompleted = idx < activeIndex;
              const isActive = idx === activeIndex;

              return (
                <div key={step.id} className="flex flex-col items-center flex-1 relative">
                  {/* Step Circle */}
                  <button
                    disabled={!isCompleted && !isActive}
                    onClick={() => setStep(step.id as any)}
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm transition-all relative z-10 border ${
                      isActive
                        ? "bg-blue-600 border-blue-500 text-white shadow-lg shadow-blue-500/20 scale-110"
                        : isCompleted
                        ? "bg-emerald-600 border-emerald-500 text-white"
                        : "bg-slate-950 border-white/5 text-slate-500"
                    }`}
                  >
                    {isCompleted ? <Check className="w-5 h-5" /> : idx + 1}
                  </button>

                  <span
                    className={`text-xs mt-2 font-medium transition-colors ${
                      isActive ? "text-blue-400 font-bold" : isCompleted ? "text-emerald-400" : "text-slate-500"
                    }`}
                  >
                    {step.label}
                  </span>

                  {/* Connecting Line */}
                  {idx < stepsToShow.length - 1 && (
                    <div
                      className={`absolute top-5 left-[50%] right-[-50%] h-[2px] z-0 transition-colors duration-300 ${
                        idx < activeIndex ? "bg-emerald-600" : "bg-slate-950"
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Content Area */}
        <div className="bg-slate-900/50 border border-white/5 rounded-3xl p-8 shadow-2xl backdrop-blur-sm min-h-[400px] flex flex-col justify-between">
          {isLoading && !rubric && !disqualifierResults && !scores ? (
            <div className="flex-1 flex flex-col items-center justify-center py-12 space-y-4">
              <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
              <p className="text-slate-400 text-sm">Loading evaluation state...</p>
            </div>
          ) : (
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.25 }}
                className="flex-grow"
              >
                {activeTab === "rubric" && (
                  <RubricEditor
                    rubric={rubric}
                    isLocked={isRubricLocked}
                    onUpdate={handleUpdateRubric}
                    onLock={handleLockRubric}
                    onRegenerate={handleRegenerateRubric}
                  />
                )}

                {activeTab === "disqualifiers" && (
                  <DisqualifierGate
                    results={disqualifierResults}
                    onContinue={() => setStep("scoring")}
                    onRegenerateSolutions={() => navigate(`/workspace/${problemId}`)}
                  />
                )}

                {activeTab === "scoring" && (
                  <ScoringTable
                    scores={scores}
                    criteria={rubric ? rubric.criteria : []}
                    onContinue={handleContinueFromScoring}
                  />
                )}

                {activeTab === "attacks" && (
                  <AttackCards
                    attacks={attacks}
                    onContinue={handleContinueFromAttacks}
                    continueText={maturitySteps.includes("ach") ? "Continue to ACH" : "Continue to Comparison"}
                  />
                )}

                {activeTab === "ach" && (
                  <ACHAnalysis
                    analysis={achAnalysis}
                    onContinue={handleContinueFromACH}
                  />
                )}

                {activeTab === "comparison" && comparison && (
                  <div className="space-y-8 animate-in fade-in">
                    <div className="space-y-2">
                      <h3 className="text-2xl font-bold text-white">Evaluation Comparison Matrix</h3>
                      <p className="text-sm text-slate-400">
                        Objective metrics aggregated from all steps. Leaders per category are highlighted.
                      </p>
                    </div>

                    {/* Table */}
                    <div className="overflow-x-auto border border-white/5 rounded-2xl shadow-xl bg-slate-900/60 max-w-full">
                      <table className="w-full border-collapse text-left min-w-[700px]">
                        <thead>
                          <tr className="border-b border-white/5 bg-slate-900/80">
                            <th className="p-4 font-semibold text-slate-400">Metric</th>
                            {comparison.entries.map((entry) => (
                              <th key={entry.solution_title} className="p-4 font-bold text-white text-center border-l border-white/5">
                                {entry.solution_title}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {/* Weighted Avg */}
                          <tr className="border-b border-white/5 hover:bg-slate-800/40">
                            <td className="p-4 font-medium text-slate-300">Weighted Average</td>
                            {comparison.entries.map((entry) => {
                              const isLeader = comparison.leaders["weighted_avg"] === entry.solution_title;
                              return (
                                <td key={entry.solution_title} className={`p-4 text-center border-l border-white/5 font-semibold ${isLeader ? "text-blue-400 bg-blue-500/5 font-bold" : "text-slate-300"}`}>
                                  {entry.weighted_avg.toFixed(2)}
                                  {isLeader && <span className="ml-2 text-[10px] bg-blue-500/10 text-blue-400 px-1.5 py-0.5 rounded-full border border-blue-500/20">Leader</span>}
                                </td>
                              );
                            })}
                          </tr>

                          {/* Min Score */}
                          <tr className="border-b border-white/5 hover:bg-slate-800/40">
                            <td className="p-4 font-medium text-slate-300">Minimum Score</td>
                            {comparison.entries.map((entry) => {
                              const isLeader = comparison.leaders["min_score"] === entry.solution_title;
                              return (
                                <td key={entry.solution_title} className={`p-4 text-center border-l border-white/5 font-semibold ${isLeader ? "text-blue-400 bg-blue-500/5 font-bold" : "text-slate-300"}`}>
                                  {entry.min_score}
                                  {isLeader && <span className="ml-2 text-[10px] bg-blue-500/10 text-blue-400 px-1.5 py-0.5 rounded-full border border-blue-500/20">Leader</span>}
                                </td>
                              );
                            })}
                          </tr>

                          {/* Attack Survival */}
                          {maturitySteps.includes("attacks") && (
                            <tr className="border-b border-white/5 hover:bg-slate-800/40">
                              <td className="p-4 font-medium text-slate-300">Worst-Case Attack Survival</td>
                              {comparison.entries.map((entry) => {
                                const isLeader = comparison.leaders["attack_survives"] === entry.solution_title;
                                return (
                                  <td key={entry.solution_title} className={`p-4 text-center border-l border-white/5 ${isLeader ? "bg-blue-500/5" : ""}`}>
                                    <div className="flex flex-col items-center gap-1">
                                      <span className={`text-xs font-semibold ${entry.attack_survives ? "text-emerald-400" : "text-red-400"}`}>
                                        {entry.attack_survives ? "Survives" : "Fails"}
                                      </span>
                                      <span className="text-[10px] text-slate-500 line-clamp-2 max-w-xs text-center">{entry.attack_summary}</span>
                                    </div>
                                  </td>
                                );
                              })}
                            </tr>
                          )}

                          {/* Inconsistency Count */}
                          {maturitySteps.includes("ach") && (
                            <tr className="hover:bg-slate-800/40">
                              <td className="p-4 font-medium text-slate-300">Evidence Inconsistencies</td>
                              {comparison.entries.map((entry) => {
                                const isLeader = comparison.leaders["inconsistency_count"] === entry.solution_title;
                                return (
                                  <td key={entry.solution_title} className={`p-4 text-center border-l border-white/5 font-semibold ${isLeader ? "text-blue-400 bg-blue-500/5 font-bold" : "text-slate-300"}`}>
                                    {entry.inconsistency_count}
                                    {isLeader && <span className="ml-2 text-[10px] bg-blue-500/10 text-blue-400 px-1.5 py-0.5 rounded-full border border-blue-500/20">Leader</span>}
                                  </td>
                                );
                              })}
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>

                    {/* Leader / Clear Winner Card */}
                    {comparison.is_clear_winner && (
                      <div className="bg-emerald-950/20 border border-emerald-500/20 rounded-2xl p-6 flex items-center gap-4 text-emerald-400">
                        <div className="p-3 bg-emerald-500/10 rounded-full border border-emerald-500/20">
                          <Check className="w-6 h-6" />
                        </div>
                        <div>
                          <h4 className="font-bold text-white text-base">Clear Winner Identified</h4>
                          <p className="text-sm text-slate-300 mt-0.5">
                            One candidate outperformed all others across every measured metric.
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Disagreement Warning */}
                    {!comparison.is_clear_winner && comparison.disagreements.length > 0 && (
                      <div className="bg-amber-950/20 border border-amber-500/20 rounded-2xl p-6 space-y-3 text-amber-400">
                        <div className="flex items-center gap-2">
                          <ShieldAlert className="w-5 h-5" />
                          <h4 className="font-bold text-white text-base">Conflict Flags (Metrics Disagree)</h4>
                        </div>
                        <ul className="space-y-1.5 text-sm text-slate-300 pl-2">
                          {comparison.disagreements.map((dis, idx) => (
                            <li key={idx} className="flex gap-2 items-start">
                              <span>•</span>
                              <span>{dis}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Bottom Actions */}
                    <div className="flex justify-end pt-4">
                      <button
                        onClick={() => navigate(`/workspace/${problemId}`)}
                        className="w-full md:w-auto px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl shadow-lg transition-all"
                      >
                        Complete Evaluation & Return
      </button>
                    </div>
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          )}
        </div>
      </div>
    </div>
  );
};

export default Evaluation;
