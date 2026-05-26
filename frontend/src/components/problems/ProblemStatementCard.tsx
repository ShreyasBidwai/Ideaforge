import React, { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { MoreVertical, Edit, Check, Archive, Calendar, User } from "lucide-react";
import { type ProblemStatement } from "../../types/api";
import { useProblemStore } from "../../stores/problemStore";
import RatingBar from "./RatingBar";
import EditProblemModal from "./EditProblemModal";

interface ProblemStatementCardProps {
  problem: ProblemStatement;
}

export const ProblemStatementCard: React.FC<ProblemStatementCardProps> = ({ problem }) => {
  const { selectProblem, archiveProblem, fetchProblems } = useProblemStore();
  const [showMenu, setShowMenu] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  
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

  const formattedDate = new Date(problem.created_at).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  const isSelected = problem.status === "selected";

  return (
    <>
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
                      setIsEditModalOpen(true);
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

      {/* Edit Modal Component */}
      <EditProblemModal
        problem={problem}
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onSave={fetchProblems}
      />
    </>
  );
};

export default ProblemStatementCard;
