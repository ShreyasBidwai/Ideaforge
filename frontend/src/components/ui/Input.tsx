import React, { forwardRef } from "react";
import { type LucideIcon } from "lucide-react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  icon?: LucideIcon;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, icon: Icon, error, type = "text", className = "", ...props }, ref) => {
    const inputId = props.id || label.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="w-full text-left space-y-1.5">
        <label htmlFor={inputId} className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
          {label}
        </label>
        <div className="relative">
          {Icon && (
            <div className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none text-slate-500">
              <Icon size={18} />
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            type={type}
            className={`
              w-full h-12 bg-slate-800/50 border rounded-xl text-white placeholder-slate-500 text-sm transition-all duration-200
              focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 outline-none
              ${Icon ? "pl-11 pr-4" : "px-4"}
              ${error ? "border-rose-500/80 focus:ring-rose-500/40 focus:border-rose-500" : "border-white/10 hover:border-white/20"}
              ${className}
            `}
            {...props}
          />
        </div>
        {error && (
          <p className="text-xs text-rose-400 animate-in fade-in slide-in-from-top-1 duration-200">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export default Input;
