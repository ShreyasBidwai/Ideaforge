import React from "react";
import { Loader2 } from "lucide-react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
}

export const Button: React.FC<ButtonProps> = ({
  children,
  isLoading,
  variant = "primary",
  size = "md",
  disabled,
  className = "",
  ...props
}) => {
  const baseStyles = "flex items-center justify-center font-semibold rounded-xl transition-all active:scale-[0.98] outline-none disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100";
  
  const variants = {
    primary: "bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-600/20",
    secondary: "bg-slate-800 border border-white/5 hover:bg-slate-700 text-white",
    ghost: "bg-transparent text-slate-300 hover:bg-white/5 hover:text-white",
  };

  const sizes = {
    sm: "h-9 px-4 text-xs",
    md: "h-12 px-6 text-sm",
    lg: "h-14 px-8 text-base",
  };

  return (
    <button
      disabled={disabled || isLoading}
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {isLoading ? (
        <>
          <Loader2 size={16} className="animate-spin mr-2" />
          <span>Please wait...</span>
        </>
      ) : (
        children
      )}
    </button>
  );
};
