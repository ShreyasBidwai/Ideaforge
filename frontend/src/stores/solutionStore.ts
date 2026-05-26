import { create } from "zustand";
import { type Solution, type ProblemStatement } from "../types/api";
import apiClient from "../services/api";
import { problemService } from "../services/problemService";

interface SolutionState {
  solutions: Solution[];
  currentProblem: ProblemStatement | null;
  isGenerating: boolean;
  isLoading: boolean;
  error: string | null;
  fetchSolutions: (problemId: string) => Promise<void>;
  generateSolutions: (problemId: string) => Promise<void>;
  approveSolution: (solutionId: string) => Promise<void>;
  clearSolutions: () => void;
}

export const useSolutionStore = create<SolutionState>((set, get) => ({
  solutions: [],
  currentProblem: null,
  isGenerating: false,
  isLoading: false,
  error: null,

  fetchSolutions: async (problemId: string) => {
    set({ isLoading: true, error: null });
    try {
      const problem = await problemService.getProblem(problemId);
      const res = await apiClient.get<Solution[]>(`/api/v1/problem-statements/${problemId}/solutions`);
      set({
        currentProblem: problem,
        solutions: res.data,
        isLoading: false
      });
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || "Failed to fetch solutions"
      });
    }
  },

  generateSolutions: async (problemId: string) => {
    set({ isGenerating: true, error: null });
    try {
      const res = await apiClient.post<Solution[]>(`/api/v1/problem-statements/${problemId}/generate-solutions`);
      set({
        solutions: res.data,
        isGenerating: false
      });
    } catch (err: any) {
      set({
        isGenerating: false,
        error: err.response?.data?.detail || "Failed to generate solutions"
      });
      throw err;
    }
  },

  approveSolution: async (solutionId: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await apiClient.post<Solution>(`/api/v1/solutions/${solutionId}/approve`);
      const updatedSolutions = get().solutions.map((sol) =>
        sol.id === solutionId ? res.data : sol
      );
      set({
        solutions: updatedSolutions,
        isLoading: false
      });
    } catch (err: any) {
      set({
        isLoading: false,
        error: err.response?.data?.detail || "Failed to approve solution"
      });
      throw err;
    }
  },

  clearSolutions: () => {
    set({
      solutions: [],
      currentProblem: null,
      error: null
    });
  }
}));
