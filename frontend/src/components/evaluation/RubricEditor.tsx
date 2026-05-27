import React, { useState } from "react";
import { Plus, Trash2, ShieldAlert, Lock, RefreshCw, X } from "lucide-react";
import type { Rubric, RubricCriterion, Disqualifier } from "../../types/api";

interface RubricEditorProps {
  rubric: Rubric | null;
  isLocked: boolean;
  onUpdate: (rubric: Rubric) => void;
  onLock: () => void;
  onRegenerate: () => void;
}

const RubricEditor: React.FC<RubricEditorProps> = ({
  rubric,
  isLocked,
  onUpdate,
  onLock,
  onRegenerate,
}) => {
  const [showLockModal, setShowLockModal] = useState(false);

  if (!rubric) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-slate-900 border border-white/5 rounded-2xl text-center space-y-6 max-w-lg mx-auto shadow-xl">
        <div className="p-4 bg-blue-500/10 text-blue-400 rounded-full">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <div className="space-y-2">
          <h3 className="text-xl font-bold text-white">Generate Evaluation Rubric</h3>
          <p className="text-sm text-slate-400">
            The AI will generate a tailored scoring rubric and disqualifier rules based on your problem statement. You can customize them before locking.
          </p>
        </div>
        <button
          onClick={onRegenerate}
          className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl shadow-lg transition-all flex items-center justify-center gap-2"
        >
          <RefreshCw className="w-5 h-5" />
          <span>Generate Rubric</span>
        </button>
      </div>
    );
  }

  const handleUpdateCriterion = (index: number, updated: Partial<RubricCriterion>) => {
    if (isLocked) return;
    const newCriteria = [...rubric.criteria];
    newCriteria[index] = { ...newCriteria[index], ...updated };
    onUpdate({ ...rubric, criteria: newCriteria });
  };

  const handleUpdateCriterionScale = (index: number, score: "1" | "3" | "5", value: string) => {
    if (isLocked) return;
    const newCriteria = [...rubric.criteria];
    newCriteria[index] = {
      ...newCriteria[index],
      scale: {
        ...newCriteria[index].scale,
        [score]: value,
      },
    };
    onUpdate({ ...rubric, criteria: newCriteria });
  };

  const handleAddCriterion = () => {
    if (isLocked || rubric.criteria.length >= 6) return;
    const newCriterion: RubricCriterion = {
      name: "New Criterion",
      description: "Description of the new criterion",
      weight: 1.0,
      scale: {
        "1": "Description for poor performance (Score 1)",
        "3": "Description for average performance (Score 3)",
        "5": "Description for excellent performance (Score 5)",
      },
    };
    onUpdate({ ...rubric, criteria: [...rubric.criteria, newCriterion] });
  };

  const handleDeleteCriterion = (index: number) => {
    if (isLocked) return;
    const newCriteria = rubric.criteria.filter((_, i) => i !== index);
    onUpdate({ ...rubric, criteria: newCriteria });
  };

  const handleUpdateDisqualifier = (index: number, updated: Partial<Disqualifier>) => {
    if (isLocked) return;
    const newDisq = [...rubric.disqualifiers];
    newDisq[index] = { ...newDisq[index], ...updated };
    onUpdate({ ...rubric, disqualifiers: newDisq });
  };

  const handleAddDisqualifier = () => {
    if (isLocked || rubric.disqualifiers.length >= 5) return;
    const newDisq: Disqualifier = {
      name: "New Disqualifier",
      description: "Conditions under which the solution should be disqualified immediately.",
    };
    onUpdate({ ...rubric, disqualifiers: [...rubric.disqualifiers, newDisq] });
  };

  const handleDeleteDisqualifier = (index: number) => {
    if (isLocked) return;
    const newDisq = rubric.disqualifiers.filter((_, i) => i !== index);
    onUpdate({ ...rubric, disqualifiers: newDisq });
  };

  return (
    <div className="space-y-8">
      {/* Criteria Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-bold text-white">Scoring Criteria</h3>
          {!isLocked && rubric.criteria.length < 6 && (
            <button
              onClick={handleAddCriterion}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-sm font-semibold transition-all flex items-center gap-1.5 border border-white/5"
            >
              <Plus className="w-4 h-4" />
              <span>Add Criterion</span>
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {rubric.criteria.map((criterion, idx) => (
            <div
              key={idx}
              className="bg-slate-900 border border-white/5 rounded-2xl p-6 relative space-y-4 shadow-lg hover:border-white/10 transition-all"
            >
              {!isLocked && (
                <button
                  onClick={() => handleDeleteCriterion(idx)}
                  className="absolute top-4 right-4 p-1.5 bg-slate-800 hover:bg-red-500/20 hover:text-red-400 rounded-lg text-slate-400 transition-all border border-white/5"
                  title="Remove Criterion"
                >
                  <X className="w-4 h-4" />
                </button>
              )}

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Criterion Name</label>
                <input
                  type="text"
                  value={criterion.name}
                  disabled={isLocked}
                  onChange={(e) => handleUpdateCriterion(idx, { name: e.target.value })}
                  className="w-full bg-slate-950 border border-white/5 rounded-xl px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 disabled:opacity-75 disabled:cursor-not-allowed"
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Description</label>
                <textarea
                  value={criterion.description}
                  disabled={isLocked}
                  onChange={(e) => handleUpdateCriterion(idx, { description: e.target.value })}
                  rows={2}
                  className="w-full bg-slate-950 border border-white/5 rounded-xl px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 resize-none disabled:opacity-75 disabled:cursor-not-allowed"
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <span>Weight Importance</span>
                  <span className="text-blue-400 font-bold">{criterion.weight.toFixed(1)}x</span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="5.0"
                  step="0.5"
                  value={criterion.weight}
                  disabled={isLocked}
                  onChange={(e) => handleUpdateCriterion(idx, { weight: parseFloat(e.target.value) })}
                  className="w-full accent-blue-500 disabled:opacity-50"
                />
              </div>

              <div className="space-y-3 pt-2 border-t border-white/5">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Scoring Anchor Definitions</label>
                <div className="space-y-2">
                  {["1", "3", "5"].map((score) => (
                    <div key={score} className="flex gap-3 items-start">
                      <span className="w-8 h-8 flex items-center justify-center bg-slate-950 border border-white/5 rounded-lg text-xs font-bold text-slate-300">
                        {score}
                      </span>
                      <textarea
                        value={criterion.scale[score as "1" | "3" | "5"] || ""}
                        disabled={isLocked}
                        onChange={(e) => handleUpdateCriterionScale(idx, score as "1" | "3" | "5", e.target.value)}
                        rows={1}
                        className="flex-1 bg-slate-950 border border-white/5 rounded-xl px-3 py-1.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 resize-none disabled:opacity-75 disabled:cursor-not-allowed"
                        placeholder={`Anchor definition for score of ${score}`}
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Disqualifiers Section */}
      <div className="space-y-4 pt-6 border-t border-white/5">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-bold text-white">Disqualifier Gates</h3>
          {!isLocked && rubric.disqualifiers.length < 5 && (
            <button
              onClick={handleAddDisqualifier}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-sm font-semibold transition-all flex items-center gap-1.5 border border-white/5"
            >
              <Plus className="w-4 h-4" />
              <span>Add Disqualifier</span>
            </button>
          )}
        </div>

        <div className="space-y-4">
          {rubric.disqualifiers.map((disq, idx) => (
            <div
              key={idx}
              className="bg-slate-900 border border-white/5 rounded-2xl p-6 relative flex flex-col md:flex-row gap-4 items-start shadow-md"
            >
              {!isLocked && (
                <button
                  onClick={() => handleDeleteDisqualifier(idx)}
                  className="absolute top-4 right-4 md:static md:self-center p-2 bg-slate-800 hover:bg-red-500/20 hover:text-red-400 rounded-xl text-slate-400 transition-all border border-white/5"
                  title="Remove Disqualifier"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}

              <div className="flex-1 w-full space-y-4 md:space-y-0 md:flex md:gap-4">
                <div className="flex-1 space-y-2">
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Gate Name</label>
                  <input
                    type="text"
                    value={disq.name}
                    disabled={isLocked}
                    onChange={(e) => handleUpdateDisqualifier(idx, { name: e.target.value })}
                    className="w-full bg-slate-950 border border-white/5 rounded-xl px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 disabled:opacity-75 disabled:cursor-not-allowed"
                  />
                </div>
                <div className="flex-[2] space-y-2">
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Gate Fail Criteria</label>
                  <input
                    type="text"
                    value={disq.description}
                    disabled={isLocked}
                    onChange={(e) => handleUpdateDisqualifier(idx, { description: e.target.value })}
                    className="w-full bg-slate-950 border border-white/5 rounded-xl px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 disabled:opacity-75 disabled:cursor-not-allowed"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Lock / Regenerate Actions */}
      <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-amber-500/10 text-amber-400 rounded-lg">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <h5 className="font-semibold text-white">Finalize Rubric Settings</h5>
            <p className="text-xs text-slate-400">Once locked, the rubric cannot be modified for this session.</p>
          </div>
        </div>

        <div className="flex gap-4 w-full md:w-auto">
          {!isLocked && (
            <>
              <button
                onClick={onRegenerate}
                className="flex-1 md:flex-none px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-xl transition-all border border-white/5 flex items-center justify-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Regenerate Rubric</span>
              </button>

              <button
                onClick={() => setShowLockModal(true)}
                className="flex-1 md:flex-none px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-blue-500/25 transition-all flex items-center justify-center gap-2"
              >
                <Lock className="w-4 h-4" />
                <span>Lock Rubric & Continue</span>
              </button>
            </>
          )}

          {isLocked && (
            <button
              onClick={onLock}
              className="w-full md:w-auto px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl shadow-lg transition-all"
            >
              <span>Continue to Disqualifier Gate</span>
            </button>
          )}
        </div>
      </div>

      {/* Lock Confirmation Modal */}
      {showLockModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-white/10 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-6 animate-in fade-in zoom-in-95">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-500/10 text-red-400 rounded-lg">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <h4 className="text-lg font-bold text-white">Lock Rubric Configuration?</h4>
            </div>

            <p className="text-sm text-slate-400">
              Are you sure? This rubric will be locked and used to evaluate all solution candidates. You cannot edit it after this step.
            </p>

            <div className="flex gap-4 justify-end">
              <button
                onClick={() => setShowLockModal(false)}
                className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-xl transition-all border border-white/5"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowLockModal(false);
                  onLock();
                }}
                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl shadow-md transition-all"
              >
                Lock Rubric
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RubricEditor;
