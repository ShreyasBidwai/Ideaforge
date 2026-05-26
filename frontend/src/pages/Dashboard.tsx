import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Layers,
  FileText,
  FlaskConical,
  CheckCircle,
  Sparkles,
  MapPin,
  ChevronRight,
  TrendingUp
} from "lucide-react";
import { useAuthStore } from "../stores/authStore";
import { useDashboardStore } from "../stores/dashboardStore";
import { useDiscoveryStore } from "../stores/discoveryStore";
import { useToastStore } from "../stores/toastStore";
import type { Session } from "../types/api";
import apiClient from "../services/api";
import ErrorBoundary from "../components/ui/ErrorBoundary";
import ErrorDisplay from "../components/ui/ErrorDisplay";
import LoadingSpinner from "../components/ui/LoadingSpinner";
import EmptyState from "../components/ui/EmptyState";

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { addToast } = useToastStore();
  const { createAndDiscover, clearSession } = useDiscoveryStore();
  
  const {
    stats,
    recentSessions,
    topProblems,
    isLoading,
    error,
    fetchDashboardData
  } = useDashboardStore();

  // Form State
  const [industry, setIndustry] = useState("");
  const [location, setLocation] = useState("");
  const [maturity, setMaturity] = useState("mvp");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Nice date string
  const formattedDate = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  const handleStartDiscovery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!industry.trim()) {
      addToast("error", "Industry is required");
      return;
    }
    if (!location.trim()) {
      addToast("error", "Location is required");
      return;
    }

    setIsSubmitting(true);
    try {
      clearSession();
      // Start discovery with empty tech stack preferences initially
      createAndDiscover(industry, location, maturity, []);
      addToast("success", "Initiating discovery session...");
      navigate("/discovery");
    } catch (err) {
      console.error(err);
      addToast("error", "Failed to start discovery session");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSessionClick = async (session: Session) => {
    if (session.status === "discovery") {
      useDiscoveryStore.setState({
        currentSession: session,
        painPoints: session.pain_points || [],
        generatedProblems: [],
        error: null
      });
      navigate("/discovery");
    } else if (session.status === "problem_generation") {
      try {
        const response = await apiClient.get(`/api/v1/sessions/${session.id}/problem-statements`);
        useDiscoveryStore.setState({
          currentSession: session,
          painPoints: session.pain_points || [],
          generatedProblems: response.data || [],
          error: null
        });
        navigate("/discovery");
      } catch (err) {
        console.error(err);
        useDiscoveryStore.setState({
          currentSession: session,
          painPoints: session.pain_points || [],
          generatedProblems: [],
          error: null
        });
        navigate("/discovery");
      }
    } else {
      // Find the problem and navigate to appropriate page
      try {
        const response = await apiClient.get(`/api/v1/sessions/${session.id}/problem-statements`);
        const problems = response.data || [];
        const selected = problems.find((p: any) => p.status === "selected") || problems[0];
        if (selected) {
          if (session.status === "solution_generation") {
            navigate(`/workspace/${selected.id}`);
          } else {
            // evaluation or completed
            navigate(`/evaluation/${selected.id}`);
          }
        } else {
          navigate("/library");
        }
      } catch (err) {
        console.error(err);
        navigate("/library");
      }
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return "Yesterday";
    return `${diffDays}d ago`;
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case "discovery":
        return "bg-blue-500/10 text-blue-400 border border-blue-500/20";
      case "problem_generation":
        return "bg-amber-500/10 text-amber-400 border border-amber-500/20";
      case "solution_generation":
        return "bg-purple-500/10 text-purple-400 border border-purple-500/20";
      case "evaluation":
        return "bg-orange-500/10 text-orange-400 border border-orange-500/20";
      case "completed":
        return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
      default:
        return "bg-slate-500/10 text-slate-400 border border-slate-500/20";
    }
  };

  const getRatingBadgeClass = (rating: number) => {
    if (rating >= 4) return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
    if (rating >= 3) return "bg-amber-500/10 text-amber-400 border border-amber-500/20";
    return "bg-rose-500/10 text-rose-400 border border-rose-500/20";
  };

  if (error) {
    return (
      <ErrorBoundary>
        <ErrorDisplay
          title="Dashboard Error"
          message={error}
          onRetry={fetchDashboardData}
        />
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <div className="w-full max-w-7xl mx-auto px-4 py-8 space-y-10 text-white">
        {/* Top Section — Welcome & Quick Stats */}
        <div className="space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                Welcome back, {user?.full_name || "Innovator"}
              </h1>
              <p className="text-slate-400 text-sm mt-1">{formattedDate}</p>
            </div>
          </div>

          {/* Stats Row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                label: "Total Sessions",
                value: stats?.sessions ?? 0,
                icon: Layers,
                color: "text-blue-500"
              },
              {
                label: "Problem Statements",
                value: stats?.problems ?? 0,
                icon: FileText,
                color: "text-indigo-500"
              },
              {
                label: "Solutions Evaluated",
                value: stats?.evaluated ?? 0,
                icon: FlaskConical,
                color: "text-violet-500"
              },
              {
                label: "Approved Solutions",
                value: stats?.approved ?? 0,
                icon: CheckCircle,
                color: "text-emerald-500"
              }
            ].map((stat, i) => {
              const Icon = stat.icon;
              return (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: i * 0.05 }}
                  className="bg-slate-800/50 backdrop-blur-sm border border-white/5 p-6 rounded-2xl flex items-center justify-between shadow-lg hover:-translate-y-1 transition-transform duration-200"
                >
                  <div className="space-y-1">
                    <div className="text-3xl font-extrabold text-white">
                      {isLoading ? <LoadingSpinner size="sm" variant="inline" /> : stat.value}
                    </div>
                    <div className="text-sm text-slate-400">{stat.label}</div>
                  </div>
                  <div className={`p-3 bg-white/5 rounded-xl border border-white/5 ${stat.color}`}>
                    <Icon size={24} />
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Middle Section — Quick Start */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="bg-gradient-to-r from-blue-600/10 to-purple-600/10 border border-blue-500/20 rounded-2xl p-6 relative overflow-hidden shadow-2xl"
        >
          <div className="absolute top-0 right-0 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl -z-10" />
          <div className="absolute bottom-0 left-0 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl -z-10" />

          <div className="flex items-center gap-2.5 mb-4">
            <Sparkles className="text-blue-400 w-5 h-5" />
            <h2 className="text-lg font-bold text-white">Start a New Discovery</h2>
          </div>

          <form onSubmit={handleStartDiscovery} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
            <div className="space-y-1.5">
              <label htmlFor="industry" className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Industry
              </label>
              <div className="relative">
                <input
                  id="industry"
                  type="text"
                  placeholder="e.g. Healthcare, Fintech"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  className="w-full h-11 bg-slate-950/60 border border-white/10 rounded-xl px-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="location" className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Location
              </label>
              <div className="relative">
                <input
                  id="location"
                  type="text"
                  placeholder="e.g. India, USA"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full h-11 bg-slate-950/60 border border-white/10 rounded-xl px-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="maturity" className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Maturity Level
              </label>
              <select
                id="maturity"
                value={maturity}
                onChange={(e) => setMaturity(e.target.value)}
                className="w-full h-11 bg-slate-950/60 border border-white/10 rounded-xl px-4 text-sm text-white focus:outline-none focus:border-blue-500 transition-all cursor-pointer"
              >
                <option value="poc">POC (Proof of Concept)</option>
                <option value="mvp">MVP (Min Viable Product)</option>
                <option value="pre_production">Pre-Production</option>
                <option value="production">Production</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="h-11 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-600/20 disabled:opacity-50"
            >
              {isSubmitting ? "Starting..." : "Discover"}
              <ChevronRight size={16} />
            </button>
          </form>
        </motion.div>

        {/* Bottom Section — Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* Left Column — Recent Sessions (60%) */}
          <div className="lg:col-span-3 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white">Recent Sessions</h3>
              <Link to="/discovery" className="text-xs font-semibold text-blue-400 hover:text-blue-300 transition-colors">
                View All
              </Link>
            </div>

            <div className="bg-slate-900/40 border border-white/5 rounded-2xl p-6 shadow-xl space-y-4 min-h-[280px] flex flex-col justify-center">
              {isLoading ? (
                <div className="flex items-center justify-center h-48">
                  <LoadingSpinner message="Loading recent sessions..." />
                </div>
              ) : recentSessions.length === 0 ? (
                <EmptyState
                  icon={Layers}
                  title="No sessions yet"
                  message="Start your first discovery above!"
                />
              ) : (
                <div className="divide-y divide-white/5 w-full">
                  {recentSessions.map((session) => (
                    <div
                      key={session.id}
                      onClick={() => handleSessionClick(session)}
                      className="py-3.5 flex items-center justify-between cursor-pointer hover:bg-white/5 px-2 rounded-xl transition-all group"
                    >
                      <div className="space-y-1">
                        <div className="font-semibold text-white group-hover:text-blue-400 transition-colors">
                          {session.industry}
                        </div>
                        <div className="flex items-center gap-1.5 text-xs text-slate-400">
                          <MapPin size={12} />
                          <span>{session.location}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-4">
                        <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider ${getStatusBadgeClass(session.status)}`}>
                          {session.status.replace("_", " ")}
                        </span>
                        <span className="text-xs text-slate-500 whitespace-nowrap min-w-[70px] text-right">
                          {formatTimeAgo(session.created_at)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column — Top Rated Problems (40%) */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white">Top Rated Problems</h3>
              <Link to="/library" className="text-xs font-semibold text-blue-400 hover:text-blue-300 transition-colors">
                View Library
              </Link>
            </div>

            <div className="bg-slate-900/40 border border-white/5 rounded-2xl p-6 shadow-xl space-y-4 min-h-[280px] flex flex-col justify-center">
              {isLoading ? (
                <div className="flex items-center justify-center h-48">
                  <LoadingSpinner message="Loading library problems..." />
                </div>
              ) : topProblems.length === 0 ? (
                <EmptyState
                  icon={FileText}
                  title="No problem statements generated"
                  message="Your generated problem statements will appear here."
                />
              ) : (
                <div className="divide-y divide-white/5 w-full">
                  {topProblems.map((problem) => (
                    <div
                      key={problem.id}
                      onClick={() => navigate(`/workspace/${problem.id}`)}
                      className="py-3.5 flex items-center justify-between cursor-pointer hover:bg-white/5 px-2 rounded-xl transition-all group"
                    >
                      <div className="space-y-1 max-w-[70%]">
                        <div className="font-semibold text-white group-hover:text-blue-400 transition-colors truncate">
                          {problem.title}
                        </div>
                        <div className="inline-block bg-slate-800 text-slate-400 text-[10px] font-bold px-2 py-0.5 rounded border border-white/5 uppercase tracking-wider font-semibold">
                          {problem.session?.industry || "Industry"}
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-extrabold px-2 py-0.5 rounded-full flex items-center gap-1 ${getRatingBadgeClass(problem.overall_rating)}`}>
                          <TrendingUp size={12} />
                          {problem.overall_rating.toFixed(1)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
};

export default Dashboard;
