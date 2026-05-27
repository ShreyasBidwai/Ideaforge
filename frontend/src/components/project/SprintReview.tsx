import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Edit2, Play, AlertTriangle, AlertCircle, CheckCircle2, Gauge, Sparkles } from 'lucide-react';

import type { Sprint as ApiSprint, SprintTask as ApiSprintTask } from '../../types/api';

interface ValidationResults {
  is_valid: boolean;
  warnings: string[];
  errors: string[];
  score: number;
}

interface Task extends ApiSprintTask {
  validation_results?: ValidationResults;
}

interface Sprint extends Omit<ApiSprint, 'tasks'> {
  tasks: Task[];
}

interface SprintReviewProps {
  sprints: Sprint[];
  onEditPrompt: (taskId: string, newPrompt: string) => void | Promise<void>;
  onApproveAndBuild: () => void | Promise<void>;
}

const SprintReview: React.FC<SprintReviewProps> = ({
  sprints,
  onEditPrompt,
  onApproveAndBuild,
}) => {
  const [expandedSprints, setExpandedSprints] = useState<Record<string, boolean>>({
    [sprints[0]?.id || '']: true,
  });
  const [expandedTasks, setExpandedTasks] = useState<Record<string, boolean>>({});
  const [editingTask, setEditingTask] = useState<string | null>(null);
  const [editPromptValue, setEditPromptValue] = useState('');

  const toggleSprint = (sprintId: string) => {
    setExpandedSprints((prev) => ({ ...prev, [sprintId]: !prev[sprintId] }));
  };

  const toggleTask = (taskId: string) => {
    setExpandedTasks((prev) => ({ ...prev, [taskId]: !prev[taskId] }));
  };

  const startEditing = (task: Task, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingTask(task.id);
    setEditPromptValue(task.prompt);
  };

  const savePrompt = async (taskId: string) => {
    await onEditPrompt(taskId, editPromptValue);
    setEditingTask(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white">Sprint Breakdown & Task Prompts</h2>
          <p className="text-sm text-zinc-400">Review and customize the task execution prompts before starting build.</p>
        </div>
        <button
          onClick={() => onApproveAndBuild()}
          className="flex items-center space-x-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-xl shadow-lg shadow-emerald-600/20 transition"
        >
          <Play className="w-4 h-4 fill-white" />
          <span>Approve Sprints & Start Build</span>
        </button>
      </div>

      <div className="space-y-4">
        {sprints.map((sprint) => {
          const isExpanded = !!expandedSprints[sprint.id];
          return (
            <div key={sprint.id} className="border border-zinc-800 bg-zinc-900/50 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleSprint(sprint.id)}
                className="w-full flex items-center justify-between px-6 py-4 bg-zinc-900 hover:bg-zinc-850/80 transition text-left"
              >
                <div className="flex items-center space-x-3">
                  {isExpanded ? <ChevronDown className="w-5 h-5 text-zinc-400" /> : <ChevronRight className="w-5 h-5 text-zinc-400" />}
                  <span className="text-sm font-semibold text-zinc-400">Sprint {sprint.sprint_number}</span>
                  <span className="text-base font-bold text-white">{sprint.name}</span>
                </div>
                <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-zinc-800 text-zinc-300 capitalize border border-zinc-700">
                  {sprint.status}
                </span>
              </button>

              {isExpanded && (
                <div className="px-6 py-4 border-t border-zinc-850 space-y-3">
                  {sprint.tasks.map((task) => {
                    const isTaskExpanded = !!expandedTasks[task.id];
                    const isEditing = editingTask === task.id;
                    return (
                      <div key={task.id} className="border border-zinc-800 bg-zinc-950/60 rounded-lg overflow-hidden">
                        <div
                          onClick={() => toggleTask(task.id)}
                          className="w-full flex items-center justify-between px-4 py-3 hover:bg-zinc-900/40 cursor-pointer transition text-left"
                        >
                          <div className="flex items-center space-x-3">
                            <span className="text-xs font-mono text-zinc-500">T{task.task_number}</span>
                            <span className="text-sm font-semibold text-zinc-200">{task.name}</span>
                            {task.validation_results && (
                              <div className="flex items-center space-x-2">
                                {task.validation_results.errors && task.validation_results.errors.length > 0 ? (
                                  <span className="flex items-center space-x-1 px-2 py-0.5 text-[10px] font-semibold rounded bg-red-950/80 text-red-400 border border-red-800/60">
                                    <AlertCircle className="w-3 h-3" />
                                    <span>{task.validation_results.errors.length} error{task.validation_results.errors.length > 1 ? 's' : ''}</span>
                                  </span>
                                ) : task.validation_results.warnings && task.validation_results.warnings.length > 0 ? (
                                  <span className="flex items-center space-x-1 px-2 py-0.5 text-[10px] font-semibold rounded bg-amber-950/80 text-amber-400 border border-amber-800/60">
                                    <AlertTriangle className="w-3 h-3" />
                                    <span>{task.validation_results.warnings.length} warning{task.validation_results.warnings.length > 1 ? 's' : ''}</span>
                                  </span>
                                ) : (
                                  <span className="flex items-center space-x-1 px-2 py-0.5 text-[10px] font-semibold rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
                                    <CheckCircle2 className="w-3 h-3" />
                                    <span>Valid</span>
                                  </span>
                                )}
                              </div>
                            )}
                          </div>
                          <div className="flex items-center space-x-2">
                            {task.validation_results && (
                              <span className="text-xs font-mono text-zinc-400 bg-zinc-900 px-2 py-0.5 rounded border border-zinc-800 flex items-center space-x-1">
                                <Gauge className="w-3 h-3 text-zinc-500" />
                                <span>Score: {Math.round(task.validation_results.score * 100)}%</span>
                              </span>
                            )}
                            <button
                              onClick={(e) => startEditing(task, e)}
                              className="p-1.5 hover:bg-zinc-850 rounded text-zinc-400 hover:text-zinc-200 transition"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                            {isTaskExpanded ? <ChevronDown className="w-4 h-4 text-zinc-500" /> : <ChevronRight className="w-4 h-4 text-zinc-500" />}
                          </div>
                        </div>

                        {isTaskExpanded && (
                          <div className="px-4 pb-4 pt-2 border-t border-zinc-900 bg-zinc-950/20">
                            {isEditing ? (
                              <div className="space-y-3">
                                <textarea
                                  value={editPromptValue}
                                  onChange={(e) => setEditPromptValue(e.target.value)}
                                  className="w-full h-48 p-3 bg-zinc-900 border border-zinc-800 rounded-lg font-mono text-xs text-zinc-200 focus:outline-none"
                                />
                                <div className="flex items-center justify-end space-x-2">
                                  <button
                                    onClick={() => setEditingTask(null)}
                                    className="px-3 py-1.5 text-xs bg-zinc-800 text-zinc-400 hover:text-zinc-200 rounded"
                                  >
                                    Cancel
                                  </button>
                                  <button
                                    onClick={() => savePrompt(task.id)}
                                    className="px-3 py-1.5 text-xs bg-indigo-600 text-white hover:bg-indigo-500 rounded"
                                  >
                                    Save Prompt
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <div className="space-y-3">
                                {task.validation_results && (task.validation_results.errors.length > 0 || task.validation_results.warnings.length > 0) && (
                                  <div className="space-y-2">
                                    {task.validation_results.errors.map((err, idx) => (
                                      <div key={idx} className="flex items-start space-x-2 p-2.5 rounded bg-red-950/45 border border-red-900/40 text-red-200 text-xs">
                                        <AlertCircle className="w-4 h-4 text-red-450 flex-shrink-0 mt-0.5" />
                                        <span>{err}</span>
                                      </div>
                                    ))}
                                    {task.validation_results.warnings.map((warn, idx) => (
                                      <div key={idx} className="flex items-start space-x-2 p-2.5 rounded bg-amber-950/45 border border-amber-900/40 text-amber-200 text-xs">
                                        <AlertTriangle className="w-4 h-4 text-amber-450 flex-shrink-0 mt-0.5" />
                                        <span>{warn}</span>
                                      </div>
                                    ))}
                                  </div>
                                )}
                                <div className="space-y-2">
                                  <div className="flex items-center justify-between">
                                    <div className="text-xs text-zinc-400 font-semibold uppercase tracking-wider">Prompt:</div>
                                    {task.validation_results && (
                                      <div className="flex items-center space-x-1.5 text-xs text-zinc-400 font-mono">
                                        <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                                        <span>Quality Score: <strong className="text-white">{Math.round(task.validation_results.score * 100)}%</strong></span>
                                      </div>
                                    )}
                                  </div>
                                  <pre className="p-3 bg-zinc-900 border border-zinc-850 rounded-lg overflow-x-auto text-xs font-mono text-zinc-300 whitespace-pre-wrap">
                                    {task.prompt}
                                  </pre>
                                </div>
                                {task.test_command && (
                                  <div className="flex items-center space-x-2 text-xs text-zinc-400 bg-zinc-900/60 px-3 py-2 rounded-lg border border-zinc-850">
                                    <span className="font-semibold text-zinc-500 uppercase tracking-wider">Test Command:</span>
                                    <code className="font-mono text-indigo-400">{task.test_command}</code>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SprintReview;
