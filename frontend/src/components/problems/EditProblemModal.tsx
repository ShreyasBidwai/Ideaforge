import React, { useState, useEffect } from "react";
import { type ProblemStatement } from "../../types/api";
import { problemService } from "../../services/problemService";
import { useToastStore } from "../../stores/toastStore";
import Modal from "../ui/Modal";
import Slider from "../ui/Slider";

interface EditProblemModalProps {
  problem: ProblemStatement;
  isOpen: boolean;
  onClose: () => void;
  onSave?: () => void;
}

export const EditProblemModal: React.FC<EditProblemModalProps> = ({
  problem,
  isOpen,
  onClose,
  onSave,
}) => {
  const { addToast } = useToastStore();
  const [loading, setLoading] = useState(false);

  // Form states
  const [title, setTitle] = useState(problem.title);
  const [description, setDescription] = useState(problem.description);
  const [targetUser, setTargetUser] = useState(problem.target_user || "");
  const [corePain, setCorePain] = useState(problem.core_pain || "");
  const [marketContext, setMarketContext] = useState(problem.market_context || "");
  
  // Rating states
  const [severity, setSeverity] = useState(problem.severity);
  const [feasibility, setFeasibility] = useState(problem.feasibility);
  const [marketSize, setMarketSize] = useState(problem.market_size);
  const [uniqueness, setUniqueness] = useState(problem.uniqueness);

  // Sync state with prop updates
  useEffect(() => {
    if (isOpen) {
      setTitle(problem.title);
      setDescription(problem.description);
      setTargetUser(problem.target_user || "");
      setCorePain(problem.core_pain || "");
      setMarketContext(problem.market_context || "");
      setSeverity(problem.severity);
      setFeasibility(problem.feasibility);
      setMarketSize(problem.market_size);
      setUniqueness(problem.uniqueness);
    }
  }, [isOpen, problem]);

  // Compute live rating
  const liveOverallRating = Math.round(((severity * 2 + feasibility * 2 + marketSize * 1.5 + uniqueness * 1) / 6.5) * 100) / 100;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !description) return;
    setLoading(true);
    try {
      await problemService.updateProblem(problem.id, {
        title,
        description,
        target_user: targetUser,
        core_pain: corePain,
        market_context: marketContext,
        severity,
        feasibility,
        market_size: marketSize,
        uniqueness,
      });
      addToast("success", "Problem statement updated successfully");
      if (onSave) {
        onSave();
      }
      onClose();
    } catch (err) {
      console.error("Failed to update problem statement:", err);
      addToast("error", "Failed to update problem statement");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Edit Problem Statement" size="2xl">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-4">
          {/* Title */}
          <div>
            <label className="block text-slate-400 text-xs font-semibold mb-1">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-slate-800 border border-white/5 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50 transition-all"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-slate-400 text-xs font-semibold mb-1">
              Description <span className="text-red-500">*</span>
            </label>
            <textarea
              required
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-slate-800 border border-white/5 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50 resize-none transition-all"
            />
          </div>

          {/* Grid for User & Pain */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-400 text-xs font-semibold mb-1">
                Target User
              </label>
              <input
                type="text"
                value={targetUser}
                onChange={(e) => setTargetUser(e.target.value)}
                className="w-full bg-slate-800 border border-white/5 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-all"
              />
            </div>
            <div>
              <label className="block text-slate-400 text-xs font-semibold mb-1">
                Core Pain
              </label>
              <input
                type="text"
                value={corePain}
                onChange={(e) => setCorePain(e.target.value)}
                className="w-full bg-slate-800 border border-white/5 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-all"
              />
            </div>
          </div>

          {/* Market Context */}
          <div>
            <label className="block text-slate-400 text-xs font-semibold mb-1">
              Market Context
            </label>
            <textarea
              rows={2}
              value={marketContext}
              onChange={(e) => setMarketContext(e.target.value)}
              className="w-full bg-slate-800 border border-white/5 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 resize-none transition-all"
            />
          </div>

          <hr className="border-white/5" />

          {/* Rating Heading */}
          <h4 className="text-sm font-bold text-white tracking-wide">
            Ratings (1-5)
          </h4>

          {/* Sliders and Preview */}
          <div className="flex flex-col lg:flex-row gap-6 items-center bg-slate-950/40 p-4 border border-white/5 rounded-2xl">
            {/* Sliders Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4 flex-1 w-full">
              <Slider
                min={1}
                max={5}
                step={0.1}
                value={severity}
                onChange={setSeverity}
                label="Severity"
              />
              <Slider
                min={1}
                max={5}
                step={0.1}
                value={feasibility}
                onChange={setFeasibility}
                label="Feasibility"
              />
              <Slider
                min={1}
                max={5}
                step={0.1}
                value={marketSize}
                onChange={setMarketSize}
                label="Market Size"
              />
              <Slider
                min={1}
                max={5}
                step={0.1}
                value={uniqueness}
                onChange={setUniqueness}
                label="Uniqueness"
              />
            </div>

            {/* Live Preview Badge */}
            <div className="flex flex-col items-center justify-center bg-slate-900 border border-white/10 w-28 h-28 rounded-2xl text-center shadow-lg px-2 flex-shrink-0">
              <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">
                Overall Rating
              </span>
              <span className="text-3xl font-extrabold text-blue-500 mt-1 font-mono">
                {liveOverallRating.toFixed(2)}
              </span>
              <span className="text-[9px] text-slate-400 mt-0.5">Live Preview</span>
            </div>
          </div>
        </div>

        {/* Footer buttons */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/5">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 border border-transparent hover:bg-slate-800 text-slate-300 hover:text-white rounded-xl text-sm font-semibold transition-all"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="flex items-center justify-center px-5 py-2 bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white rounded-xl text-sm font-semibold shadow-lg shadow-blue-600/20 disabled:opacity-50 transition-all min-w-[120px]"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              "Save Changes"
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default EditProblemModal;
