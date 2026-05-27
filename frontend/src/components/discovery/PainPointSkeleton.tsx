import React from "react";

export const PainPointSkeleton: React.FC = () => {
  return (
    <div className="bg-slate-800/50 border border-white/5 rounded-2xl p-6 space-y-4 animate-pulse">
      <div className="flex items-center gap-4">
        <div className="h-6 bg-slate-700 rounded-full w-12" />
        <div className="h-6 bg-slate-700 rounded w-2/3" />
      </div>
      <div className="space-y-2">
        <div className="h-4 bg-slate-700 rounded w-full" />
        <div className="h-4 bg-slate-700 rounded w-5/6" />
        <div className="h-4 bg-slate-700 rounded w-2/3" />
      </div>
      <div className="pt-2 flex justify-between items-center gap-4">
        <div className="flex gap-2">
          <div className="h-5 bg-slate-700 rounded-full w-16" />
          <div className="h-5 bg-slate-700 rounded-full w-20" />
        </div>
        <div className="h-4 bg-slate-700 rounded w-1/3" />
      </div>
    </div>
  );
};

export default PainPointSkeleton;
