import React from "react";
import { motion } from "framer-motion";

interface ViewToggleProps {
  view: "cards" | "compare";
  onChange: (view: "cards" | "compare") => void;
}

const ViewToggle: React.FC<ViewToggleProps> = ({ view, onChange }) => {
  return (
    <div className="relative flex items-center p-1 bg-slate-900/80 border border-white/5 rounded-xl">
      {/* Sliding background */}
      <motion.div
        className="absolute top-1 bottom-1 bg-blue-600 rounded-lg shadow-md"
        initial={false}
        animate={{
          left: view === "cards" ? "4px" : "50%",
          right: view === "cards" ? "50%" : "4px",
        }}
        transition={{ type: "spring", stiffness: 400, damping: 30 }}
      />

      {/* Cards Option Button */}
      <button
        onClick={() => onChange("cards")}
        className={`relative z-10 w-28 py-1.5 text-xs font-semibold rounded-lg focus:outline-none transition-colors duration-200 ${
          view === "cards" ? "text-white" : "text-slate-400 hover:text-white"
        }`}
      >
        Cards
      </button>

      {/* Compare Option Button */}
      <button
        onClick={() => onChange("compare")}
        className={`relative z-10 w-28 py-1.5 text-xs font-semibold rounded-lg focus:outline-none transition-colors duration-200 ${
          view === "compare" ? "text-white" : "text-slate-400 hover:text-white"
        }`}
      >
        Compare
      </button>
    </div>
  );
};

export default ViewToggle;
