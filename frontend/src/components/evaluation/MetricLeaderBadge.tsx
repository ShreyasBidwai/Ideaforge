import React from "react";
import { Star } from "lucide-react";

const MetricLeaderBadge: React.FC = () => {
  return (
    <span className="inline-flex items-center gap-1 bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider">
      <Star className="w-3 h-3 fill-amber-400" />
      <span>Leader</span>
    </span>
  );
};

export default MetricLeaderBadge;
