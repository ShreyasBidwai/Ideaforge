import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, Check, Sparkles } from "lucide-react";

interface ProblemGenerationProgressProps {
  currentStep: string;
}

const STEPS = [
  { key: "analyzing", label: "Analyzing pain points", description: "Mapping selected pain points for synthesis" },
  { key: "generating", label: "Generating problem statements", description: "Querying Gemini to frame structured problems" },
  { key: "rating", label: "Computing ratings", description: "Estimating severity, feasibility, market size, and uniqueness" },
  { key: "saving", label: "Saving to library", description: "Saving to your library" },
  { key: "complete", label: "Complete", description: "All problem statements synthesized successfully" },
];

export const ProblemGenerationProgress: React.FC<ProblemGenerationProgressProps> = ({
  currentStep,
}) => {
  const currentIndex = STEPS.findIndex((s) => s.key === currentStep);

  return (
    <div className="w-full max-w-xl mx-auto bg-slate-950/40 backdrop-blur-xl border border-white/5 rounded-3xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
      {/* Decorative blurs */}
      <div className="absolute top-0 right-0 w-48 h-48 bg-blue-500/10 rounded-full blur-3xl -z-10" />
      <div className="absolute bottom-0 left-0 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl -z-10" />

      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-blue-500/10 rounded-xl text-blue-400 border border-blue-500/20">
          <Sparkles className="w-5 h-5 animate-pulse" />
        </div>
        <div>
          <h3 className="text-white font-bold text-lg">AI Problem Synthesizer</h3>
          <p className="text-slate-400 text-xs sm:text-sm">Synthesizing pain points into opportunities</p>
        </div>
      </div>

      <div className="relative space-y-6 pl-4 border-l-2 border-slate-800">
        {STEPS.map((step, idx) => {
          const isDone = idx < currentIndex;
          const isActive = idx === currentIndex;

          return (
            <div key={step.key} className="relative flex items-start gap-4 group">
              {/* Icon */}
              <div className="absolute -left-[29px] mt-0.5 flex items-center justify-center">
                <AnimatePresence mode="wait">
                  {isDone ? (
                    <motion.div
                      key="done"
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.8, opacity: 0 }}
                      className="w-5 h-5 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-lg shadow-emerald-500/20"
                    >
                      <Check className="w-3 h-3" strokeWidth={3} />
                    </motion.div>
                  ) : isActive ? (
                    <motion.div
                      key="active"
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.8, opacity: 0 }}
                      className="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center shadow-lg shadow-blue-600/30"
                    >
                      <Loader2 className="w-3 h-3 animate-spin" />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="pending"
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.8, opacity: 0 }}
                      className="w-5 h-5 rounded-full bg-slate-900 border-2 border-slate-700 flex items-center justify-center"
                    >
                      <div className="w-1.5 h-1.5 rounded-full bg-slate-700" />
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Text */}
              <div className="flex-1">
                <div
                  className={`text-sm font-semibold transition-colors duration-200 ${
                    isActive ? "text-blue-400" : isDone ? "text-slate-300" : "text-slate-500"
                  }`}
                >
                  {step.label}
                </div>
                <div
                  className={`text-xs transition-colors duration-200 mt-0.5 ${
                    isActive ? "text-slate-300" : isDone ? "text-slate-400" : "text-slate-600"
                  }`}
                >
                  {step.description}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ProblemGenerationProgress;
