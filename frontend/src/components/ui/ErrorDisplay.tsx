import React from "react";
import { AlertTriangle } from "lucide-react";
import { Link } from "react-router-dom";

interface ErrorDisplayProps {
  title: string;
  message: string;
  onRetry?: () => void;
  showHome?: boolean;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  title,
  message,
  onRetry,
  showHome = false
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-slate-900/50 border border-white/5 rounded-2xl max-w-md mx-auto my-6 shadow-xl text-white">
      <div className="w-12 h-12 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center justify-center text-red-500 mb-4">
        <AlertTriangle size={24} />
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-slate-400 text-sm leading-relaxed mb-6">{message}</p>
      
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-center w-full">
        {onRetry && (
          <button
            onClick={onRetry}
            className="w-full sm:w-auto px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-blue-600/20 transition-all"
          >
            Try Again
          </button>
        )}
        {showHome && (
          <Link
            to="/"
            className="w-full sm:w-auto px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold border border-white/5 text-center transition-all"
          >
            Back to Dashboard
          </Link>
        )}
      </div>
    </div>
  );
};

export default ErrorDisplay;
