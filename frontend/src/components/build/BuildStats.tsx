import React from 'react';
import { Layers, CheckCircle2, ListTodo, Clock } from 'lucide-react';

interface BuildStatsProps {
  stats: {
    completedTasks: number;
    totalTasks: number;
    testsPassing: number;
    eta: string;
  };
  currentSprint?: string;
  totalSprints?: string;
}

export default function BuildStats({ stats, currentSprint = "1", totalSprints = "4" }: BuildStatsProps) {
  const taskProgress = stats.totalTasks > 0 ? Math.round((stats.completedTasks / stats.totalTasks) * 100) : 0;
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Current Sprint */}
      <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 backdrop-blur-sm shadow-lg flex items-center justify-between">
        <div>
          <p className="text-slate-400 text-xs font-medium uppercase tracking-wider font-mono">Current Sprint</p>
          <p className="text-2xl font-bold text-slate-100 mt-2">{currentSprint} <span className="text-slate-500 text-sm">/ {totalSprints}</span></p>
        </div>
        <div className="p-3 bg-blue-500/10 text-blue-400 rounded-lg border border-blue-500/20">
          <Layers className="w-5 h-5" />
        </div>
      </div>

      {/* Tasks Progress */}
      <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 backdrop-blur-sm shadow-lg flex items-center justify-between">
        <div>
          <p className="text-slate-400 text-xs font-medium uppercase tracking-wider font-mono">Tasks Completed</p>
          <div className="flex items-baseline space-x-2 mt-2">
            <span className="text-2xl font-bold text-slate-100">{stats.completedTasks}</span>
            <span className="text-slate-500 text-sm">/ {stats.totalTasks}</span>
            <span className="text-blue-400 text-xs font-semibold bg-blue-500/10 px-2 py-0.5 rounded-full border border-blue-500/10">{taskProgress}%</span>
          </div>
        </div>
        <div className="p-3 bg-purple-500/10 text-purple-400 rounded-lg border border-purple-500/20">
          <ListTodo className="w-5 h-5" />
        </div>
      </div>

      {/* Tests Passing */}
      <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 backdrop-blur-sm shadow-lg flex items-center justify-between">
        <div>
          <p className="text-slate-400 text-xs font-medium uppercase tracking-wider font-mono">Tests Passing</p>
          <p className="text-2xl font-bold text-emerald-400 mt-2">{stats.testsPassing}</p>
        </div>
        <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-lg border border-emerald-500/20">
          <CheckCircle2 className="w-5 h-5" />
        </div>
      </div>

      {/* ETA */}
      <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 backdrop-blur-sm shadow-lg flex items-center justify-between">
        <div>
          <p className="text-slate-400 text-xs font-medium uppercase tracking-wider font-mono">Estimated Time</p>
          <p className="text-2xl font-bold text-slate-100 mt-2">{stats.eta}</p>
        </div>
        <div className="p-3 bg-amber-500/10 text-amber-400 rounded-lg border border-amber-500/20">
          <Clock className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}
