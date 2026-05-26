import React from "react";
import { Loader2 } from "lucide-react";

interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
  message?: string;
  variant?: "full-page" | "inline" | "default";
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = "md",
  message,
  variant = "default"
}) => {
  const sizeClasses = {
    sm: "w-4 h-4",
    md: "w-8 h-8",
    lg: "w-12 h-12"
  };

  const spinner = (
    <Loader2 className={`${sizeClasses[size]} animate-spin text-blue-500`} />
  );

  if (variant === "full-page") {
    return (
      <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center space-y-4">
        {spinner}
        {message && <p className="text-slate-400 text-sm font-medium">{message}</p>}
      </div>
    );
  }

  if (variant === "inline") {
    return (
      <span className="inline-flex items-center gap-2 text-slate-400 text-sm">
        {spinner}
        {message && <span>{message}</span>}
      </span>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center py-12 w-full space-y-3">
      {spinner}
      {message && <p className="text-slate-400 text-sm font-medium">{message}</p>}
    </div>
  );
};

export default LoadingSpinner;
