import { create } from "zustand";
import type { Session, ProblemStatement } from "../types/api";
import apiClient from "../services/api";
import sessionService from "../services/sessionService";
import problemService from "../services/problemService";

interface DashboardState {
  stats: { sessions: number; problems: number; evaluated: number; approved: number; } | null;
  recentSessions: Session[];
  topProblems: ProblemStatement[];
  isLoading: boolean;
  fetchDashboardData: () => Promise<void>;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  stats: null,
  recentSessions: [],
  topProblems: [],
  isLoading: false,
  fetchDashboardData: async () => {
    set({ isLoading: true });
    try {
      // Fetch stats
      const statsRes = await apiClient.get("/api/v1/dashboard/stats");
      const stats = {
        sessions: statsRes.data.total_sessions || 0,
        problems: statsRes.data.total_problems || 0,
        evaluated: statsRes.data.solutions_evaluated || 0,
        approved: statsRes.data.solutions_approved || 0,
      };

      // Fetch sessions
      const sessions = await sessionService.getUserSessions();
      const recentSessions = sessions.slice(0, 5);

      // Fetch top rated problems
      const problemsRes = await problemService.getProblems({
        sort_by: "overall_rating",
        sort_order: "desc",
        per_page: 5,
      });
      const topProblems = problemsRes.items || [];

      set({ stats, recentSessions, topProblems, isLoading: false });
    } catch (error) {
      console.error("Error loading dashboard data:", error);
      set({ isLoading: false });
    }
  },
}));
