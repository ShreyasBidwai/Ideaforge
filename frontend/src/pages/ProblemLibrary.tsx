import React from "react";
import { motion } from "framer-motion";
import { Library } from "lucide-react";

const ProblemLibrary: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-md w-full bg-slate-900/50 backdrop-blur-sm border border-white/5 p-8 rounded-2xl text-center space-y-4 shadow-2xl"
      >
        <div className="mx-auto w-16 h-16 bg-blue-600/10 rounded-2xl flex items-center justify-center border border-blue-500/20 text-blue-500">
          <Library size={32} />
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
          Problem Library
        </h1>
        <p className="text-slate-400 text-sm">Coming in Sprint 2</p>
      </motion.div>
    </div>
  );
};

export default ProblemLibrary;
