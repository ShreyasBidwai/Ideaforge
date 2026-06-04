import { create } from "zustand";
import { type CompetitorAnalysis } from "../types/api";
import apiClient from "../services/api";
import { useToastStore } from "./toastStore";

interface CompetitorState {
  analyses: Record<string, CompetitorAnalysis>;
  isLoading: boolean;
  error: string | null;
  fetchAnalysis: (solutionId: string) => Promise<CompetitorAnalysis | null>;
  runAnalysis: (solutionId: string) => Promise<CompetitorAnalysis | null>;
  refreshAnalysis: (solutionId: string) => Promise<CompetitorAnalysis | null>;
  clearAnalysis: (solutionId: string) => void;
}

export const useCompetitorStore = create<CompetitorState>((set, get) => ({
  analyses: {},
  isLoading: false,
  error: null,

  fetchAnalysis: async (solutionId: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await apiClient.get<CompetitorAnalysis>(
        `/api/v1/solutions/${solutionId}/competitor-analysis`
      );
      set((state) => ({
        analyses: { ...state.analyses, [solutionId]: res.data },
        isLoading: false,
      }));
      return res.data;
    } catch (err: any) {
      const errMsg = err.response?.data?.detail || "Failed to fetch competitor analysis";
      set({ isLoading: false, error: errMsg });
      return null;
    }
  },

  runAnalysis: async (solutionId: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await apiClient.post<CompetitorAnalysis>(
        `/api/v1/solutions/${solutionId}/competitor-analysis/run`
      );
      set((state) => ({
        analyses: { ...state.analyses, [solutionId]: res.data },
        isLoading: false,
      }));
      useToastStore.getState().addToast("info", "Started researching competitors in the background...");
      return res.data;
    } catch (err: any) {
      const errMsg = err.response?.data?.detail || "Failed to run competitor analysis";
      set({ isLoading: false, error: errMsg });
      useToastStore.getState().addToast("error", errMsg);
      return null;
    }
  },

  refreshAnalysis: async (solutionId: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await apiClient.post<CompetitorAnalysis>(
        `/api/v1/solutions/${solutionId}/competitor-analysis/refresh`
      );
      set((state) => ({
        analyses: { ...state.analyses, [solutionId]: res.data },
        isLoading: false,
      }));
      useToastStore.getState().addToast("info", "Refreshing competitor research in the background...");
      return res.data;
    } catch (err: any) {
      const errMsg = err.response?.data?.detail || "Failed to refresh competitor analysis";
      set({ isLoading: false, error: errMsg });
      useToastStore.getState().addToast("error", errMsg);
      return null;
    }
  },

  clearAnalysis: (solutionId: string) => {
    set((state) => {
      const newAnalyses = { ...state.analyses };
      delete newAnalyses[solutionId];
      return { analyses: newAnalyses };
    });
  },
}));
