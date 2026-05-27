import React, { useState, useEffect } from 'react';
import { Timer, ShieldCheck } from 'lucide-react';

interface RateLimitCountdownProps {
  resumeAt: string;
}

export const RateLimitCountdown: React.FC<RateLimitCountdownProps> = ({ resumeAt }) => {
  const [timeLeft, setTimeLeft] = useState<string>('');
  const [progressPercent, setProgressPercent] = useState<number>(0);

  useEffect(() => {
    const target = new Date(resumeAt).getTime();
    if (isNaN(target)) {
      setTimeLeft('Calculated time...');
      return;
    }

    const interval = setInterval(() => {
      const now = new Date().getTime();
      const diff = target - now;

      if (diff <= 0) {
        setTimeLeft('Resuming shortly...');
        setProgressPercent(100);
        clearInterval(interval);
        return;
      }

      // Format time
      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);

      const parts = [];
      if (hours > 0) parts.push(`${hours}h`);
      if (minutes > 0 || hours > 0) parts.push(`${minutes}m`);
      parts.push(`${seconds}s`);

      setTimeLeft(parts.join(' '));

      // Calculate progress assuming a standard max wait of 1 hour (3600000ms)
      const waitTotal = 3600000;
      const elapsed = Math.max(0, waitTotal - diff);
      setProgressPercent(Math.min(100, (elapsed / waitTotal) * 100));
    }, 1000);

    return () => clearInterval(interval);
  }, [resumeAt]);

  return (
    <div className="bg-zinc-950 border border-amber-900/40 rounded-xl p-6 shadow-xl max-w-md mx-auto space-y-5 text-center">
      <div className="space-y-1">
        <div className="mx-auto w-12 h-12 bg-amber-950/40 border border-amber-900/30 rounded-full flex items-center justify-center text-amber-500 mb-2">
          <Timer className="w-6 h-6 animate-pulse" />
        </div>
        <h3 className="text-sm font-bold text-amber-200">Build Paused — Claude Code rate limit reached</h3>
        <p className="text-zinc-400 text-xs">
          The API rate limits have been hit. Orchestrator will resume building once reset.
        </p>
      </div>

      <div className="py-2.5">
        <div className="text-3xl font-extrabold text-white tracking-tight font-mono">{timeLeft || 'Calculating...'}</div>
        <div className="text-[10px] text-zinc-500 uppercase font-semibold mt-1">Estimated Resume Time: {new Date(resumeAt).toLocaleTimeString()}</div>
      </div>

      {/* Progress bar */}
      <div className="space-y-1.5 text-left">
        <div className="w-full bg-zinc-900 rounded-full h-2 overflow-hidden border border-zinc-800">
          <div
            className="bg-amber-550 h-full rounded-full transition-all duration-1000 ease-out"
            style={{ width: `${Math.max(5, progressPercent)}%` }}
          />
        </div>
      </div>

      <div className="flex items-center space-x-2.5 bg-zinc-900 border border-zinc-850 p-3.5 rounded-lg text-left">
        <ShieldCheck className="w-5 h-5 text-indigo-400 flex-shrink-0" />
        <span className="text-xs text-zinc-300">
          Your progress is saved. You can close this page and come back later; the build will run in the background.
        </span>
      </div>
    </div>
  );
};

export default RateLimitCountdown;
