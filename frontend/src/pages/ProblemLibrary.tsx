import React, { useEffect } from "react";
import { Link } from "react-router-dom";
import { Library, Plus, ChevronLeft, ChevronRight, Award, FolderHeart, ListPlus } from "lucide-react";
import { useProblemStore } from "../stores/problemStore";
import ProblemStatementCard from "../components/problems/ProblemStatementCard";
import ProblemFilters from "../components/problems/ProblemFilters";
import EmptyLibrary from "../components/problems/EmptyLibrary";
import Skeleton from "../components/ui/Skeleton";

export const ProblemLibrary: React.FC = () => {
  const {
    problems,
    total,
    page,
    filters,
    industries,
    isLoading,
    fetchProblems,
    fetchIndustries,
    setFilters,
    setPage,
  } = useProblemStore();

  useEffect(() => {
    fetchProblems();
    fetchIndustries();
  }, []); // Run once on mount

  // Client-side search filter on loaded data
  const filteredProblems = problems.filter((p) => {
    if (!filters.search) return true;
    const query = filters.search.toLowerCase();
    return (
      p.title.toLowerCase().includes(query) ||
      p.description.toLowerCase().includes(query)
    );
  });

  // Calculate local stats from loaded problems
  const selectedCount = problems.filter((p) => p.status === "selected").length;
  const avgRating =
    problems.length > 0
      ? (problems.reduce((sum, p) => sum + p.overall_rating, 0) / problems.length).toFixed(1)
      : "0.0";

  const totalPages = Math.ceil(total / 20) || 1;
  const startItem = total === 0 ? 0 : (page - 1) * 20 + 1;
  const endItem = Math.min(page * 20, total);

  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans selection:bg-blue-600/30 selection:text-blue-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
        
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-500">
                <Library className="w-5 h-5" />
              </div>
              <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
                Problem Library
              </h1>
            </div>
            <p className="text-slate-400 text-sm">
              All discovered problem statements across your sessions
            </p>
          </div>

          <Link
            to="/discovery"
            className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white rounded-xl font-semibold shadow-lg shadow-blue-600/20 transition-all self-start md:self-auto"
          >
            <Plus className="w-4 h-4" />
            <span>New Discovery</span>
          </Link>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-slate-900/50 border border-white/5 rounded-2xl p-5 flex items-center gap-4 backdrop-blur-md">
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400 border border-blue-500/15">
              <ListPlus className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Total Problems</p>
              <h4 className="text-2xl font-bold text-white mt-0.5">{total}</h4>
            </div>
          </div>

          <div className="bg-slate-900/50 border border-white/5 rounded-2xl p-5 flex items-center gap-4 backdrop-blur-md">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400 border border-emerald-500/15">
              <FolderHeart className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Selected (Visible)</p>
              <h4 className="text-2xl font-bold text-white mt-0.5">{selectedCount}</h4>
            </div>
          </div>

          <div className="bg-slate-900/50 border border-white/5 rounded-2xl p-5 flex items-center gap-4 backdrop-blur-md">
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-400 border border-amber-500/15">
              <Award className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Avg Page Rating</p>
              <h4 className="text-2xl font-bold text-white mt-0.5">{avgRating}</h4>
            </div>
          </div>
        </div>

        {/* Filters/Sort bar */}
        <ProblemFilters
          industries={industries}
          filters={filters}
          onChange={(newFilters) => setFilters(newFilters)}
        />

        {/* Loading Indicator */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="bg-slate-900/40 border border-white/5 rounded-2xl p-6 space-y-4">
                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-2 flex-1">
                    <Skeleton className="h-6 w-3/4" />
                    <Skeleton className="h-4 w-1/3" />
                  </div>
                  <Skeleton className="h-6 w-12 rounded-full" />
                </div>
                <Skeleton className="h-16 w-full" />
                <div className="flex flex-wrap gap-2 pt-2">
                  <Skeleton className="h-5 w-16 rounded-full" />
                  <Skeleton className="h-5 w-20 rounded-full" />
                  <Skeleton className="h-5 w-24 rounded-full" />
                </div>
                <div className="flex justify-between items-center pt-4 border-t border-white/5">
                  <Skeleton className="h-5 w-24" />
                  <Skeleton className="h-9 w-28 rounded-xl" />
                </div>
              </div>
            ))}
          </div>
        ) : filteredProblems.length === 0 ? (
          <EmptyLibrary />
        ) : (
          <div className="space-y-6">
            {/* Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredProblems.map((prob) => (
                <ProblemStatementCard key={prob.id} problem={prob} />
              ))}
            </div>

            {/* Pagination controls */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 border-t border-white/5 text-sm text-slate-400">
              <p>
                Showing <span className="text-white font-medium">{startItem}</span> to{" "}
                <span className="text-white font-medium">{endItem}</span> of{" "}
                <span className="text-white font-medium">{total}</span> problems
              </p>
              
              <div className="flex items-center gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                  className="p-2 bg-slate-900 border border-white/5 rounded-lg text-slate-400 hover:text-white hover:border-white/10 disabled:opacity-50 disabled:hover:text-slate-400 disabled:hover:border-white/5 transition-all"
                  title="Previous page"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>

                <div className="hidden sm:flex items-center gap-1.5 px-3">
                  <span className="text-white font-semibold">{page}</span>
                  <span className="text-slate-600">/</span>
                  <span className="text-slate-500">{totalPages}</span>
                </div>

                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage(page + 1)}
                  className="p-2 bg-slate-900 border border-white/5 rounded-lg text-slate-400 hover:text-white hover:border-white/10 disabled:opacity-50 disabled:hover:text-slate-400 disabled:hover:border-white/5 transition-all"
                  title="Next page"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default ProblemLibrary;
