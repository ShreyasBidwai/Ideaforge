import React from "react";

interface RatingBarProps {
  label: string;
  value: number;
  maxValue?: number;
}

export const RatingBar: React.FC<RatingBarProps> = ({
  label,
  value,
  maxValue = 5,
}) => {
  const percentage = Math.max(0, Math.min(100, (value / maxValue) * 100));

  let colorClass = "bg-green-500";
  if (value < 2) {
    colorClass = "bg-red-500";
  } else if (value <= 3.5) {
    colorClass = "bg-amber-500";
  }

  return (
    <div className="flex items-center justify-between gap-3 text-xs w-full">
      <span className="text-slate-500 font-medium w-10">{label}</span>
      <div className="flex-1 h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${colorClass}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-slate-300 font-semibold w-6 text-right">
        {value.toFixed(1)}
      </span>
    </div>
  );
};

export default RatingBar;
