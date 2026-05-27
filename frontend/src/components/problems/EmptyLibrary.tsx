import React from "react";
import { Link } from "react-router-dom";
import { Lightbulb } from "lucide-react";

export const EmptyLibrary: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center text-center p-12 bg-slate-900/50 border border-white/5 rounded-3xl max-w-lg mx-auto mt-12 backdrop-blur-md">
      <div className="w-16 h-16 rounded-2xl bg-blue-600/10 flex items-center justify-center mb-6 text-blue-500 border border-blue-500/20">
        <Lightbulb className="w-8 h-8" />
      </div>
      <h3 className="text-xl font-bold text-white mb-2">No problem statements yet</h3>
      <p className="text-slate-400 text-sm mb-8 max-w-sm">
        Start a discovery session to generate your first problem statements.
      </p>
      <Link
        to="/discovery"
        className="px-6 py-3 bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white rounded-xl font-semibold shadow-lg shadow-blue-600/25 transition-all"
      >
        Start Discovery
      </Link>
    </div>
  );
};

export default EmptyLibrary;
