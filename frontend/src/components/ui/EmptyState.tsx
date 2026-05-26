import React from "react";
import { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  message,
  actionLabel,
  onAction
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center bg-slate-900/30 border border-white/5 rounded-3xl max-w-xl mx-auto shadow-xl space-y-5">
      {Icon ? (
        <div className="w-16 h-16 bg-slate-800/80 border border-white/5 rounded-2xl flex items-center justify-center text-slate-500">
          <Icon size={48} className="text-slate-600" />
        </div>
      ) : null}
      
      <div className="space-y-2">
        <h3 className="text-lg font-bold text-white">{title}</h3>
        <p className="text-slate-400 text-sm leading-relaxed max-w-md mx-auto">
          {message}
        </p>
      </div>

      {actionLabel && onAction ? (
        <button
          onClick={onAction}
          className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl text-sm shadow-lg shadow-blue-600/20 hover:shadow-blue-500/30 transition-all flex items-center gap-2 hover:-translate-y-0.5 active:translate-y-0"
        >
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
};

export default EmptyState;
