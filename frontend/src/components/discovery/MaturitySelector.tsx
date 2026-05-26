import React from "react";
import { motion } from "framer-motion";
import { Zap, Rocket, Shield, Building2 } from "lucide-react";

interface MaturitySelectorProps {
  value: string;
  onChange: (value: string) => void;
  levels?: Array<{
    level: string;
    label: string;
    description: string;
  }>;
}

const DEFAULT_LEVELS = [
  { level: "poc", label: "POC", description: "Quick validation" },
  { level: "mvp", label: "MVP", description: "Balanced depth" },
  { level: "pre_production", label: "Pre-Prod", description: "Full rigor" },
  { level: "production", label: "Production", description: "Enterprise-ready" },
];

export const MaturitySelector: React.FC<MaturitySelectorProps> = ({
  value,
  onChange,
  levels = DEFAULT_LEVELS,
}) => {
  const getIcon = (levelName: string) => {
    const name = levelName.toLowerCase();
    if (name.includes("poc")) return Zap;
    if (name.includes("mvp")) return Rocket;
    if (name.includes("pre")) return Shield;
    return Building2;
  };

  const getStats = (levelName: string) => {
    const name = levelName.toLowerCase();
    if (name.includes("poc")) return "3 solutions, light eval";
    if (name.includes("mvp")) return "4 solutions, standard eval";
    if (name.includes("pre")) return "5 solutions, detailed eval";
    return "6 solutions, full eval + attack";
  };

  return (
    <div className="w-full space-y-3">
      <label className="text-slate-400 text-xs font-semibold uppercase tracking-wider block">
        Project Maturity Level
      </label>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {levels.map((lvl) => {
          const isSelected = value === lvl.level;
          const Icon = getIcon(lvl.level);
          const stats = getStats(lvl.level);

          return (
            <motion.button
              key={lvl.level}
              type="button"
              onClick={() => onChange(lvl.level)}
              animate={isSelected ? "selected" : "unselected"}
              variants={{
                selected: { scale: 1.02 },
                unselected: { scale: 1 },
              }}
              transition={{ type: "spring", stiffness: 300, damping: 20 }}
              style={{
                boxShadow: isSelected ? "0 0 20px rgba(37,99,235,0.15)" : "none",
              }}
              className={`flex flex-col items-start text-left p-4 rounded-2xl border transition-all duration-200 cursor-pointer w-full h-full justify-between ${
                isSelected
                  ? "border-blue-600 bg-blue-600/10 text-white"
                  : "border-white/5 bg-slate-800/30 text-slate-400 hover:border-white/10 hover:text-slate-300"
              }`}
            >
              <div className="w-full">
                <div className="flex items-center justify-between mb-3 w-full">
                  <div
                    className={`p-2 rounded-lg ${
                      isSelected ? "bg-blue-600 text-white" : "bg-slate-900 text-slate-400"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  {isSelected && (
                    <div className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse" />
                  )}
                </div>
                <h4 className="text-white font-bold text-sm sm:text-base mb-1">
                  {lvl.label}
                </h4>
                <p className="text-slate-400 text-xs leading-normal mb-3">
                  {lvl.description}
                </p>
              </div>
              <div className="text-[10px] sm:text-xs font-semibold uppercase tracking-wider text-blue-400/80">
                {stats}
              </div>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
};

export default MaturitySelector;
