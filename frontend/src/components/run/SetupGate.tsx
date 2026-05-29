import React, { useState, useEffect } from "react";
import { Check, ExternalLink, HelpCircle, Save } from "lucide-react";
import { type SetupStep } from "../../stores/runStore";

interface SetupGateProps {
  steps: SetupStep[];
  onReady: () => void;
  onSave: (stepId: string, value: string) => void | Promise<void>;
  onMark: (stepId: string, completed: boolean) => void | Promise<void>;
}

export default function SetupGate({ steps, onReady, onSave, onMark }: SetupGateProps) {
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<Record<string, boolean>>({});

  const requiredSteps = steps.filter((s) => s.is_required);
  const completedRequiredSteps = requiredSteps.filter((s) => s.is_completed);

  const totalRequired = requiredSteps.length;
  const completedRequired = completedRequiredSteps.length;

  useEffect(() => {
    if (totalRequired > 0 && completedRequired === totalRequired) {
      onReady();
    }
  }, [completedRequired, totalRequired, onReady]);

  const handleInputChange = (stepId: string, value: string) => {
    setInputs((prev) => ({ ...prev, [stepId]: value }));
  };

  const handleSaveClick = async (stepId: string) => {
    const val = inputs[stepId] || "";
    setSaving((prev) => ({ ...prev, [stepId]: true }));
    try {
      await onSave(stepId, val);
      setInputs((prev) => ({ ...prev, [stepId]: "" }));
    } catch (e) {
      console.error(e);
    } finally {
      setSaving((prev) => ({ ...prev, [stepId]: false }));
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
      {/* Title & Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-lg font-bold text-white font-mono uppercase tracking-wider">Human Setup Checklist Gate</h3>
          <p className="text-sm text-slate-400 mt-1">
            Configure required settings to unlock project runner.
          </p>
        </div>
        <div className="bg-slate-950 px-4 py-2 rounded-lg border border-slate-800 flex items-center space-x-2">
          <span className="text-xs font-semibold text-slate-400 font-mono">
            {completedRequired} of {totalRequired} required steps complete
          </span>
          {completedRequired === totalRequired && (
            <span className="p-1 bg-emerald-500/10 text-emerald-400 rounded-full">
              <Check className="w-3.5 h-3.5" />
            </span>
          )}
        </div>
      </div>

      {/* Steps List */}
      <div className="space-y-4">
        {steps.length === 0 ? (
          <p className="text-sm text-slate-500 font-mono text-center py-6">
            No setup steps defined for this project.
          </p>
        ) : (
          steps.map((step) => {
            const isCompleted = step.is_completed;
            const isApiKeyOrEnvVar = step.step_type === "api_key" || step.step_type === "env_var";

            return (
              <div
                key={step.id}
                className={`p-4 rounded-lg border transition-all ${
                  isCompleted
                    ? "bg-slate-950/40 border-slate-800/80 text-slate-300"
                    : "bg-slate-900/50 border-slate-800 text-slate-100"
                }`}
              >
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                  {/* Header / Info */}
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                      <span className="text-sm font-bold text-white">{step.title}</span>
                      {step.is_required && (
                        <span className="bg-red-500/10 text-red-400 border border-red-500/20 text-[10px] px-1.5 py-0.5 rounded font-mono uppercase">
                          Required
                        </span>
                      )}
                      <span className="bg-slate-800 text-slate-400 text-[10px] px-1.5 py-0.5 rounded font-mono uppercase">
                        {step.step_type.replace("_", " ")}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed">{step.description}</p>
                    {step.env_key && (
                      <span className="inline-block bg-slate-950 text-slate-400 text-[11px] px-2 py-0.5 rounded font-mono border border-slate-850 mt-1">
                        {step.env_key}
                      </span>
                    )}
                  </div>

                  {/* Action Zone */}
                  <div className="w-full md:w-auto flex items-center gap-3">
                    {isApiKeyOrEnvVar ? (
                      <div className="w-full md:w-72 flex items-center space-x-2">
                        <input
                          type="password"
                          value={inputs[step.id] || ""}
                          placeholder={isCompleted ? "•••••••• (Saved)" : "Enter value..."}
                          onChange={(e) => handleInputChange(step.id, e.target.value)}
                          className="flex-1 bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono"
                        />
                        <button
                          onClick={() => handleSaveClick(step.id)}
                          disabled={saving[step.id]}
                          className="bg-blue-600 hover:bg-blue-500 text-white rounded px-3 py-1.5 text-xs font-semibold flex items-center space-x-1.5 transition-colors disabled:opacity-50"
                        >
                          <Save className="w-3.5 h-3.5" />
                          <span>{saving[step.id] ? "Saving..." : "Save"}</span>
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center space-x-3">
                        {step.doc_url && (
                          <a
                            href={step.doc_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs font-semibold text-blue-400 hover:text-blue-300 transition-colors flex items-center space-x-1 font-mono"
                          >
                            <span>Setup Instructions</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                        <label className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={isCompleted}
                            onChange={(e) => onMark(step.id, e.target.checked)}
                            className="w-4 h-4 rounded border-slate-800 bg-slate-950 text-blue-600 focus:ring-blue-500 focus:ring-offset-slate-900"
                          />
                          <span className="text-xs font-semibold text-slate-350">Mark completed</span>
                        </label>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
