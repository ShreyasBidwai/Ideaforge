import React from 'react';
import { motion } from 'framer-motion';

interface BuildProgressProps {
  progress: number;
}

export default function BuildProgress({ progress }: BuildProgressProps) {
  const roundedProgress = Math.min(100, Math.max(0, Math.round(progress)));

  return (
    <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-5 backdrop-blur-sm shadow-md">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium text-slate-300 font-mono">Overall Progress</span>
        <span className="text-sm font-bold text-blue-400 font-mono">{roundedProgress}%</span>
      </div>
      <div className="w-full bg-slate-900 rounded-full h-3 overflow-hidden border border-slate-800">
        <motion.div
          className="bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-600 h-full rounded-full shadow-[0_0_8px_rgba(59,130,246,0.5)]"
          initial={{ width: 0 }}
          animate={{ width: `${roundedProgress}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}
