import React from "react";
import { Lightbulb } from "lucide-react";

interface GenerateSolutionsCTAProps {
  onGenerate: () => void;
  solutionCount?: number;
  isGenerating?: boolean;
}

const GenerateSolutionsCTA: React.FC<GenerateSolutionsCTAProps> = ({
  onGenerate,
  solutionCount = 4,
  isGenerating = false
}) => {
  return (
    <div className="flex flex-col items-center justify-center border border-white/5 bg-slate-800/20 rounded-2xl p-12 text-center max-w-xl mx-auto shadow-xl backdrop-blur-sm mt-8">
      <div className="w-16 h-16 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-6 animate-pulse">
        <Lightbulb className="w-8 h-8" />
      </div>
      
      <h3 className="text-xl font-semibold text-white mb-2">No Solution Candidates Yet</h3>
      <p className="text-slate-400 mb-8 max-w-sm">
        AI will generate {solutionCount} diverse solutions including at least one unconventional approach following the Idea Evaluation Protocol.
      </p>

      <button
        onClick={onGenerate}
        disabled={isGenerating}
        className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium shadow-lg hover:shadow-blue-500/20 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
      >
        {isGenerating ? (
          <>
            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Generating Solutions...
          </>
        ) : (
          "Generate Solution Candidates"
        )}
      </button>
    </div>
  );
};

export default GenerateSolutionsCTA;
