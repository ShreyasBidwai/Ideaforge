import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

interface RateLimitGaugeProps {
  info: {
    isLimited: boolean;
    resumeAt: string | null;
    usage: number;
    capacity: number;
  } | null;
}

export default function RateLimitGauge({ info }: RateLimitGaugeProps) {
  if (!info) return null;

  const usagePercent = Math.min(100, Math.round((info.usage / info.capacity) * 100));

  return (
    <div className="bg-slate-800/30 border border-slate-700/50 rounded-xl p-5 backdrop-blur-sm shadow-md">
      <div className="flex justify-between items-start mb-4">
        <div>
          <span className="text-sm font-medium text-slate-300 font-mono">Claude Code Capacity</span>
          <p className="text-xs text-slate-500 mt-0.5">Estimated usage rate of tokens and requests</p>
        </div>
        <div className="text-right">
          <span className="text-sm font-bold text-slate-200 font-mono">{info.usage}</span>
          <span className="text-xs text-slate-500 font-mono"> / {info.capacity} req/hr</span>
        </div>
      </div>

      {info.isLimited ? (
        <div className="bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-lg p-3 flex items-start space-x-3 mb-4">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider">Rate Limit Hit</p>
            <p className="text-xs text-amber-300/95 mt-0.5">
              Paused — resuming at {info.resumeAt || "7:00 PM"}
            </p>
          </div>
        </div>
      ) : (
        <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg p-3 flex items-start space-x-3 mb-4">
          <ShieldCheck className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider font-mono">Optimal State</p>
            <p className="text-xs text-emerald-300/95 mt-0.5 font-mono">
              Operating within safety limits.
            </p>
          </div>
        </div>
      )}

      {/* Progress Bar Gauge */}
      <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            info.isLimited ? 'bg-amber-500' : usagePercent > 80 ? 'bg-red-500' : 'bg-blue-500'
          }`}
          style={{ width: `${usagePercent}%` }}
        />
      </div>
    </div>
  );
}
