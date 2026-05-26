import React from "react";

interface SliderProps {
  min: number;
  max: number;
  step: number;
  value: number;
  onChange: (value: number) => void;
  label: string;
  showValue?: boolean;
}

export const Slider: React.FC<SliderProps> = ({
  min,
  max,
  step,
  value,
  onChange,
  label,
  showValue = true,
}) => {
  return (
    <div className="space-y-2 w-full">
      <div className="flex justify-between items-center text-xs font-semibold">
        <label className="text-slate-400">{label}</label>
        {showValue && (
          <span className="text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-md font-mono border border-blue-500/15">
            {value.toFixed(1)}
          </span>
        )}
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-500/30"
      />
    </div>
  );
};

export default Slider;
