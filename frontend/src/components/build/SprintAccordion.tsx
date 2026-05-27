import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp, CheckCircle, Clock, Loader2, XCircle, RotateCcw } from 'lucide-react';
import type { Sprint, SprintTask } from '../../types/api';

interface SprintAccordionProps {
  sprints: Sprint[];
}

export default function SprintAccordion({ sprints }: SprintAccordionProps) {
  const [expandedSprintId, setExpandedSprintId] = useState<string | null>(null);

  const toggleSprint = (sprintId: string) => {
    setExpandedSprintId(expandedSprintId === sprintId ? null : sprintId);
  };

  const getSprintBadge = (status: string) => {
    switch (status) {
      case "complete":
      case "completed":
        return <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full text-xs">Complete</span>;
      case "running":
      case "building":
      case "in_progress":
        return <span className="bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full text-xs animate-pulse">Active</span>;
      default:
        return <span className="bg-slate-800 text-slate-400 border border-slate-700/60 px-2 py-0.5 rounded-full text-xs">Pending</span>;
    }
  };

  const getTaskIcon = (task: SprintTask) => {
    switch (task.status) {
      case "passed":
      case "complete":
        return <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />;
      case "running":
        return <Loader2 className="w-4 h-4 text-blue-400 animate-spin flex-shrink-0" />;
      case "retrying":
        return (
          <div className="flex items-center space-x-1 text-amber-400 flex-shrink-0">
            <RotateCcw className="w-3.5 h-3.5 animate-spin" />
            <span className="text-[10px] font-bold">R1</span>
          </div>
        );
      case "failed":
        return <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />;
      default:
        return <Clock className="w-4 h-4 text-slate-500 flex-shrink-0" />;
    }
  };

  return (
    <div className="space-y-3">
      {sprints.map((sprint) => {
        const isExpanded = expandedSprintId === sprint.id;
        
        return (
          <div
            key={sprint.id}
            className="border border-slate-700/50 rounded-xl overflow-hidden bg-slate-800/20 backdrop-blur-sm shadow-md"
          >
            {/* Sprint Header */}
            <button
              onClick={() => toggleSprint(sprint.id)}
              className="w-full px-5 py-4 flex items-center justify-between hover:bg-slate-700/10 transition-colors"
            >
              <div className="flex items-center space-x-3">
                <span className="text-sm font-semibold text-slate-200 font-mono">
                  Sprint {sprint.sprint_number}: {sprint.name}
                </span>
                {getSprintBadge(sprint.status)}
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-xs text-slate-500 font-mono">
                  {sprint.tasks?.length || 0} Tasks
                </span>
                {isExpanded ? (
                  <ChevronUp className="w-4 h-4 text-slate-400" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-slate-400" />
                )}
              </div>
            </button>

            {/* Task List */}
            <AnimatePresence>
              {isExpanded && (
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: "auto" }}
                  exit={{ height: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden bg-slate-900/30 border-t border-slate-700/30"
                >
                  <div className="p-4 space-y-2">
                    {sprint.tasks && sprint.tasks.length > 0 ? (
                      sprint.tasks.map((task) => {
                        const isRunning = task.status === "running" || task.status === "retrying";
                        const isFailed = task.status === "failed";
                        
                        return (
                          <div
                            key={task.id}
                            className={`flex items-center justify-between p-3 rounded-lg border text-sm transition-all ${
                              isRunning
                                ? "bg-blue-500/5 border-blue-500/20 text-blue-100"
                                : isFailed
                                ? "bg-red-500/5 border-red-500/20 text-red-100"
                                : "bg-slate-900/40 border-slate-800/80 text-slate-300"
                            }`}
                          >
                            <div className="flex items-center space-x-3">
                              {getTaskIcon(task)}
                              <span className="font-medium text-xs font-mono text-slate-400 mr-1">
                                T{task.task_number}
                              </span>
                              <span>{task.name}</span>
                            </div>
                            <div className="flex items-center space-x-3 text-xs text-slate-500 font-mono">
                              {task.test_count > 0 && (
                                <span className={`${task.tests_failed > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                                  {task.tests_passed} / {task.test_count} tests
                                </span>
                              )}
                              {task.status === "passed" && (
                                <span className="bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/10 text-[10px] uppercase font-bold font-mono">Passed</span>
                              )}
                              {task.status === "failed" && (
                                <span className="bg-red-500/10 text-red-400 px-1.5 py-0.5 rounded border border-red-500/10 text-[10px] uppercase font-bold font-mono">Failed</span>
                              )}
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <p className="text-xs text-slate-500 text-center py-2 font-mono">No tasks available in this sprint.</p>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
}
