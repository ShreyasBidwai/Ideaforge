import React from "react";
import { motion } from "framer-motion";
import { type PainPoint } from "../../types/api";

interface PainPointCardProps {
  painPoint: PainPoint;
  index?: number;
}

export const PainPointCard: React.FC<PainPointCardProps> = ({ painPoint, index = 0 }) => {
  const { name, description, severity, affected_stakeholders, evidence } = painPoint;

  const getSeverityStyles = (sev: number) => {
    if (sev <= 3) {
      return "bg-green-500/10 text-green-400 border border-green-500/20";
    }
    if (sev <= 6) {
      return "bg-amber-500/10 text-amber-400 border border-amber-500/20";
    }
    return "bg-red-500/10 text-red-400 border border-red-500/20";
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.1 }}
      whileHover={{ y: -2, transition: { duration: 0.15 } }}
      className="bg-slate-900/50 backdrop-blur-md border border-white/5 rounded-2xl p-6 hover:shadow-xl hover:shadow-blue-500/5 hover:border-white/10 transition-all flex flex-col justify-between"
    >
      <div>
        <div className="flex items-start gap-3 mb-3">
          <span className={`inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-xs font-semibold shrink-0 ${getSeverityStyles(severity)}`}>
            Sev {severity}
          </span>
          <h3 className="text-white font-semibold text-lg leading-snug">{name}</h3>
        </div>
        <p className="text-slate-300 text-sm leading-relaxed mb-4">{description}</p>
      </div>

      <div className="space-y-3 pt-3 border-t border-white/5">
        <div className="flex flex-wrap gap-1.5">
          {affected_stakeholders.map((stakeholder, i) => (
            <span key={i} className="bg-slate-800/80 text-slate-300 text-xs px-2 py-0.5 rounded-md border border-white/5">
              {stakeholder}
            </span>
          ))}
        </div>
        {evidence && (
          <p className="text-slate-400 italic text-xs leading-normal">
            <span className="font-semibold text-slate-500 not-italic uppercase tracking-wider text-[10px] mr-1">Evidence:</span>
            {evidence}
          </p>
        )}
      </div>
    </motion.div>
  );
};

export default PainPointCard;
