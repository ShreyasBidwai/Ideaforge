import React, { useState } from "react";
import { ArrowUpDown, Search, SlidersHorizontal, ChevronDown, ChevronUp } from "lucide-react";

interface ProblemFiltersProps {
  industries: string[];
  filters: {
    industry: string | null;
    status: string | null;
    sortBy: string;
    sortOrder: string;
    search: string;
  };
  onChange: (filters: Partial<ProblemFiltersProps["filters"]>) => void;
}

export const ProblemFilters: React.FC<ProblemFiltersProps> = ({
  industries,
  filters,
  onChange,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between bg-slate-900/40 p-4 border border-white/5 rounded-2xl backdrop-blur-md w-full">
      {/* Search and Mobile Toggle Row */}
      <div className="flex items-center gap-2 w-full md:w-auto">
        <div className="relative flex-grow md:w-80">
          <span className="absolute inset-y-0 left-3 flex items-center text-slate-500">
            <Search className="w-4 h-4" />
          </span>
          <input
            type="text"
            placeholder="Search problems..."
            value={filters.search}
            onChange={(e) => onChange({ search: e.target.value })}
            className="w-full bg-slate-800/80 border border-white/5 rounded-xl pl-10 pr-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50 text-sm transition-all"
          />
        </div>
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex md:hidden items-center gap-1.5 bg-slate-800/80 hover:bg-slate-700/80 border border-white/5 rounded-xl px-3.5 py-2.5 text-white text-sm font-semibold focus:outline-none transition-all"
        >
          <SlidersHorizontal className="w-4 h-4 text-slate-400" />
          <span>Filters</span>
          {isExpanded ? <ChevronUp className="w-3.5 h-3.5 text-slate-400" /> : <ChevronDown className="w-3.5 h-3.5 text-slate-400" />}
        </button>
      </div>

      {/* Select filters */}
      <div className={`${isExpanded ? "flex" : "hidden"} md:flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full md:w-auto justify-end`}>
        {/* Industry */}
        <select
          value={filters.industry || ""}
          onChange={(e) => onChange({ industry: e.target.value || null })}
          className="bg-slate-800/80 border border-white/5 rounded-xl px-3 py-2.5 sm:py-2 text-white text-sm focus:outline-none focus:border-blue-500/50 transition-all cursor-pointer min-w-[130px]"
        >
          <option value="">All Industries</option>
          {industries.map((ind) => (
            <option key={ind} value={ind}>
              {ind}
            </option>
          ))}
        </select>

        {/* Status */}
        <select
          value={filters.status || ""}
          onChange={(e) => onChange({ status: e.target.value || null })}
          className="bg-slate-800/80 border border-white/5 rounded-xl px-3 py-2.5 sm:py-2 text-white text-sm focus:outline-none focus:border-blue-500/50 transition-all cursor-pointer"
        >
          <option value="">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="selected">Selected</option>
          <option value="archived">Archived</option>
        </select>

        {/* Sort By */}
        <select
          value={filters.sortBy}
          onChange={(e) => onChange({ sortBy: e.target.value })}
          className="bg-slate-800/80 border border-white/5 rounded-xl px-3 py-2.5 sm:py-2 text-white text-sm focus:outline-none focus:border-blue-500/50 transition-all cursor-pointer"
        >
          <option value="overall_rating">Rating</option>
          <option value="severity">Severity</option>
          <option value="feasibility">Feasibility</option>
          <option value="market_size">Market Size</option>
          <option value="uniqueness">Uniqueness</option>
          <option value="created_at">Date</option>
        </select>

        {/* Sort Order Toggle */}
        <button
          onClick={() => onChange({ sortOrder: filters.sortOrder === "desc" ? "asc" : "desc" })}
          className="flex items-center justify-center gap-1.5 bg-slate-800/80 hover:bg-slate-700/80 active:bg-slate-800/80 border border-white/5 rounded-xl px-3 py-2.5 sm:py-2 text-white text-sm focus:outline-none focus:border-blue-500/50 transition-all"
          title="Toggle sort direction"
        >
          <ArrowUpDown className="w-4 h-4 text-slate-400" />
          <span>{filters.sortOrder === "asc" ? "↑ asc" : "↓ desc"}</span>
        </button>
      </div>
    </div>
  );
};

export default ProblemFilters;
