import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface MaturitySelectorProps {
  value: string;
  onChange: (value: string) => void;
}

interface LevelInfo {
  id: string;
  label: string;
  description: string;
}

const levels: LevelInfo[] = [
  {
    id: "poc",
    label: "POC",
    description: "Proof of Concept: Quick discovery. 3 pain points, temperature 0.9.",
  },
  {
    id: "mvp",
    label: "MVP",
    description: "Minimum Viable Product: Balanced depth. 5 pain points, temperature 0.7.",
  },
  {
    id: "pre_production",
    label: "Pre-Prod",
    description: "Pre-Production: High rigor. 6-8 pain points, temperature 0.5.",
  },
  {
    id: "production",
    label: "Production",
    description: "Production: Ultimate depth & validation. 8-10 pain points, temperature 0.3.",
  },
];

export const MaturitySelector: React.FC<MaturitySelectorProps> = ({ value, onChange }) => {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <div className="relative w-full space-y-2">
      <label className="text-slate-400 text-xs font-semibold uppercase tracking-wider">
        Project Maturity Level
      </label>
      
      <div className="flex bg-slate-900 border border-white/5 rounded-xl p-1 gap-1">
        {levels.map((level) => {
          const isSelected = value === level.id;
          return (
            <div
              key={level.id}
              className="relative flex-1"
              onMouseEnter={() => setHoveredId(level.id)}
              onMouseLeave={() => setHoveredId(null)}
            >
              <button
                type="button"
                onClick={() => onChange(level.id)}
                className={`w-full relative py-2.5 text-xs sm:text-sm font-semibold rounded-lg transition-colors z-10 ${
                  isSelected
                    ? "bg-blue-600 text-white"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {isSelected && (
                  <motion.span
                    layoutId="active-maturity"
                    className="absolute inset-0 bg-blue-600 rounded-lg -z-10"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
                {level.label}
              </button>

              <AnimatePresence>
                {hoveredId === level.id && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    transition={{ duration: 0.15 }}
                    className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 z-50 w-60 bg-slate-950 border border-white/10 p-3 rounded-xl shadow-2xl text-xs text-slate-300 pointer-events-none"
                  >
                    <div className="font-semibold text-white mb-1">{level.label} Mode</div>
                    <div>{level.description}</div>
                    <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-950" />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default MaturitySelector;
