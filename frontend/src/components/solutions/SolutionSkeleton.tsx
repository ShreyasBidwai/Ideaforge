import React from "react";

const SolutionSkeleton: React.FC = () => {
  const skeletons = Array.from({ length: 3 });

  return (
    <div className="space-y-6 w-full">
      {skeletons.map((_, index) => (
        <div
          key={index}
          className="bg-slate-800/30 border border-white/5 rounded-2xl p-6 animate-pulse space-y-4"
        >
          {/* Header Row skeleton */}
          <div className="flex justify-between items-center">
            <div className="h-6 w-1/3 bg-slate-700/50 rounded" />
            <div className="h-5 w-20 bg-slate-700/50 rounded-full" />
          </div>

          {/* Description skeleton */}
          <div className="space-y-2">
            <div className="h-4 w-full bg-slate-700/50 rounded" />
            <div className="h-4 w-5/6 bg-slate-700/50 rounded" />
          </div>

          {/* Mechanism skeleton */}
          <div className="space-y-2 pt-2">
            <div className="h-3 w-16 bg-slate-700/50 rounded" />
            <div className="h-16 w-full bg-slate-700/30 rounded-xl" />
          </div>

          {/* Tech stack skeleton */}
          <div className="flex gap-2">
            <div className="h-7 w-20 bg-slate-700/50 rounded-lg" />
            <div className="h-7 w-24 bg-slate-700/50 rounded-lg" />
            <div className="h-7 w-16 bg-slate-700/50 rounded-lg" />
          </div>

          {/* Bottom row skeleton */}
          <div className="flex gap-6 pt-4 border-t border-white/5">
            <div className="h-4 w-28 bg-slate-700/50 rounded" />
            <div className="h-4 w-24 bg-slate-700/50 rounded" />
          </div>
        </div>
      ))}
    </div>
  );
};

export default SolutionSkeleton;
