import React, { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { MoreVertical, Edit, Check, Archive, Calendar, User, Save, X } from "lucide-react";
import { type ProblemStatement } from "../../types/api";
import { useProblemStore } from "../../stores/problemStore";
import RatingBar from "./RatingBar";

interface ProblemStatementCardProps {
  problem: ProblemStatement;
}

export const ProblemStatementCard: React.FC<ProblemStatementCardProps> = ({ problem }) => {
  const { selectProblem, archiveProblem, fetchProblems } = useProblemStore();
  const [showMenu, setShowMenu] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  
  // Edit form states
  const [title, setTitle] = useState(problem.title);
  const [description, setDescription] = useState(problem.description);
  const [targetUser, setTargetUser] = useState(problem.target_user || "");
  const [corePain, setCorePain] = useState(problem.core_pain || "");
  const [marketContext, setMarketContext] = useState(problem.market_context || "");
  const [severity, setSeverity] = useState(problem.severity);
  const [feasibility, setFeasibility] = useState(problem.feasibility);
  const [marketSize, setMarketSize] = useState(problem.market_size);
  const [uniqueness, setUniqueness] = useState(problem.uniqueness);

  const menuRef = useRef<HTMLDivElement>(null);

  // Close overflow menu if clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Top border rating color coding
  let ratingColor = "bg-green-500";
  if (problem.overall_rating < 2.5) {
    ratingColor = "bg-red-500";
  } else if (problem.overall_rating <= 3.5) {
    ratingColor = "bg-amber-500";
  }

  // Circular rating badge color coding
  let ratingBadgeColor = "text-green-400 border-green-500/30 bg-green-500/10";
  if (problem.overall_rating < 2.5) {
    ratingBadgeColor = "text-red-400 border-red-500/30 bg-red-500/10";
  } else if (problem.overall_rating <= 3.5) {
    ratingBadgeColor = "text-amber-400 border-amber-500/30 bg-amber-500/10";
  }

  const handleSelect = async () => {
    setShowMenu(false);
    await selectProblem(problem.id);
  };

  const handleArchive = async () => {
    setShowMenu(false);
    await archiveProblem(problem.id);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const { problemService } = await import("../../services/problemService");
      await problemService.updateProblem(problem.id, {
        title,
        description,
        target_user: targetUser,
        core_pain: corePain,
        market_context: marketContext,
        severity,
        feasibility,
        market_size,
        uniqueness,
      });
      setIsEditing(false);
      await fetchProblems();
    } catch (err) {
      console.error("Failed to update problem statement:", err);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    // Reset states
    setTitle(problem.title);
    setDescription(problem.description);
    setTargetUser(problem.target_user || "");
    setCorePain(problem.core_pain || "");
    setMarketContext(problem.market_context || "");
    setSeverity(problem.severity);
    setFeasibility(problem.feasibility);
    setMarketSize(problem.market_size);
    setUniqueness(problem.uniqueness);
  };

  const formattedDate = new Date(problem.created_at).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  const isSelected = problem.status === "selected";

  if (isEditing) {
    return (
      <motion.div
        layout
        className="bg-slate-800/80 border border-blue-500/30 rounded-2xl p-5 shadow-2xl relative"
      >
        <div className="absolute top-0 left-0 right-0 h-1 bg-blue-500 rounded-t-2xl" />
        <h4 className="text-white font-bold text-base mb-4 flex items-center justify-between">
          <span>Edit Problem Statement</span>
          <button onClick={handleCancel} className="text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </h4>
        <form onSubmit={handleSave} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-400 mb-1 font-semibold">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              className="w-full bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
            />
          </div>
          <div>
            <label className="block text-slate-400 mb-1 font-semibold">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              rows={3}
              className="w-full bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50 resize-none text-xs"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 mb-1 font-semibold">Target User</label>
              <input
                type="text"
                value={targetUser}
                onChange={(e) => setTargetUser(e.target.value)}
                className="w-full bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500/50"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-semibold">Core Pain</label>
              <input
                type="text"
                value={corePain}
                onChange={(e) => setCorePain(e.target.value)}
                className="w-full bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500/50"
              />
            </div>
          </div>
          <div>
            <label className="block text-slate-400 mb-1 font-semibold">Market Context</label>
            <input
              type="text"
              value={marketContext}
              onChange={(e) => setMarketContext(e.target.value)}
              className="w-full bg-slate-900 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500/50"
            />
          </div>

          <div className="bg-slate-900/60 p-3 rounded-xl border border-white/5 space-y-2">
            <h5 className="font-semibold text-slate-400 mb-1">Ratings (1-5)</h5>
            <div className="grid grid-cols-2 gap-x-4 gap-y-2">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Severity:</span>
                <input
                  type="number"
                  min="1"
                  max="5"
                  step="0.1"
                  value={severity}
                  onChange={(e) => setSeverity(parseFloat(e.target.value))}
                  className="w-12 bg-slate-950 border border-white/10 rounded text-center text-white py-0.5"
                />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Feasibility:</span>
                <input
                  type="number"
                  min="1"
                  max="5"
                  step="0.1"
                  value={feasibility}
                  onChange={(e) => setFeasibility(parseFloat(e.target.value))}
                  className="w-12 bg-slate-950 border border-white/10 rounded text-center text-white py-0.5"
                />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Market Size:</span>
                <input
                  type="number"
                  min="1"
                  max="5"
                  step="0.1"
                  value={marketSize}
                  onChange={(e) => setMarketSize(parseFloat(e.target.value))}
                  className="w-12 bg-slate-950 border border-white/10 rounded text-center text-white py-0.5"
                />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Uniqueness:</span>
                <input
                  type="number"
                  min="1"
                  max="5"
                  step="0.1"
                  value={uniqueness}
                  onChange={(e) => setUniqueness(parseFloat(e.target.value))}
                  className="w-12 bg-slate-950 border border-white/10 rounded text-center text-white py-0.5"
                />
              </div>
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-white/5">
            <button
              type="button"
              onClick={handleCancel}
              className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-semibold transition-all"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Save</span>
            </button>
          </div>
        </form>
      </motion.div>
    );
  }

  return (
    <motion.div
      layout
      whileHover={{ y: -4, borderColor: "rgba(255,255,255,0.1)" }}
      className={`bg-slate-800/50 border border-white/5 rounded-2xl overflow-hidden shadow-lg transition-all duration-300 flex flex-col justify-between relative ${
        isSelected ? "border-l-[3px] border-l-emerald-500" : ""
      }`}
    >
      {/* Top Rating-colored Stripe */}
      <div className={`h-1 w-full ${ratingColor}`} />

      {/* Card Body */}
      <div className="p-5 flex-1 flex flex-col">
        {/* Header & Tag & Status Badge */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="flex flex-col gap-1.5 items-start">
            <span className="bg-blue-600/20 text-blue-400 px-2 py-0.5 rounded-full text-[10px] font-semibold tracking-wide uppercase">
              {problem.industry || "General"}
            </span>
            <h3 className="text-base font-bold text-white leading-snug line-clamp-2">
              {problem.title}
            </h3>
          </div>

          {/* Action Menu & Selected Status */}
          <div className="flex items-center gap-1.5 relative" ref={menuRef}>
            {isSelected && (
              <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider">
                Selected
              </span>
            )}
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-700/50 transition-all focus:outline-none"
              aria-label="Actions"
            >
              <MoreVertical className="w-4 h-4" />
            </button>

            {/* Overflow Dropdown */}
            {showMenu && (
              <div className="absolute right-0 top-7 w-32 bg-slate-900 border border-white/10 rounded-xl shadow-2xl py-1 z-20">
                <button
                  onClick={() => {
                    setShowMenu(false);
                    setIsEditing(true);
                  }}
                  className="w-full px-3 py-2 text-left text-xs text-slate-300 hover:bg-slate-800 hover:text-white flex items-center gap-2"
                >
                  <Edit className="w-3.5 h-3.5" />
                  <span>Edit</span>
                </button>
                {!isSelected && (
                  <button
                    onClick={handleSelect}
                    className="w-full px-3 py-2 text-left text-xs text-slate-300 hover:bg-slate-800 hover:text-white flex items-center gap-2"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Select</span>
                  </button>
                )}
                {problem.status !== "archived" && (
                  <button
                    onClick={handleArchive}
                    className="w-full px-3 py-2 text-left text-xs text-red-400 hover:bg-slate-800 hover:text-red-300 flex items-center gap-2"
                  >
                    <Archive className="w-3.5 h-3.5" />
                    <span>Archive</span>
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Description */}
        <p className="text-slate-300 text-xs mb-5 line-clamp-3 leading-relaxed flex-1">
          {problem.description}
        </p>

        {/* Rating Metrics & Overall Rating Badge */}
        <div className="flex gap-4 items-center bg-slate-900/30 p-3 rounded-xl border border-white/5 mb-4">
          <div className="flex-1 space-y-2">
            <RatingBar label="SEV" value={problem.severity} />
            <RatingBar label="FEAS" value={problem.feasibility} />
            <RatingBar label="MKT" value={problem.market_size} />
            <RatingBar label="UNIQ" value={problem.uniqueness} />
          </div>

          <div
            className={`w-12 h-12 rounded-full border flex flex-col items-center justify-center font-bold text-sm shadow-md ${ratingBadgeColor}`}
            title="Overall Rating"
          >
            <span>{problem.overall_rating.toFixed(1)}</span>
            <span className="text-[7px] text-slate-500 -mt-0.5">SCORE</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-5 py-3.5 bg-slate-900/40 border-t border-white/5 flex items-center justify-between text-[10px] text-slate-500">
        <div className="flex items-center gap-1 max-w-[60%]">
          <User className="w-3 h-3 text-slate-600 flex-shrink-0" />
          <span className="truncate" title={problem.target_user || "Unspecified"}>
            {problem.target_user || "Unspecified"}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <Calendar className="w-3 h-3 text-slate-600" />
          <span>{formattedDate}</span>
        </div>
      </div>
    </motion.div>
  );
};

export default ProblemStatementCard;
