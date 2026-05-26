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
  currentStep?: string;
  progressMessage?: string;
  fetchSolutions: (problemId: string) => Promise<void>;
  generateSolutions: (problemId: string) => Promise<void>;
  approveSolution: (solutionId: string) => Promise<void>;
  updateSolution: (solutionId: string, updates: Partial<Solution>) => Promise<void>;
  clearSolutions: () => void;
}

export const useSolutionStore = create<SolutionState>((set, get) => ({
  solutions: [],
  currentProblem: null,
  isGenerating: false,
  isLoading: false,
  error: null,
  currentStep: "",
  progressMessage: "",

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
    set({ isGenerating: true, error: null, currentStep: "starting", progressMessage: "Initializing..." });
    try {
      const { streamSolutions } = await import("../services/streamService");
      await streamSolutions(
        problemId,
        (status, message) => {
          set({ currentStep: status, progressMessage: message });
        },
        (sols) => {
          set({
            solutions: sols,
            isGenerating: false,
            currentStep: "complete",
            progressMessage: ""
          });
        },
        (err) => {
          set({
            isGenerating: false,
            error: err,
            currentStep: "",
            progressMessage: ""
          });
        }
      );
    } catch (err: any) {
      set({
        isGenerating: false,
        error: err.message || "Failed to generate solutions",
        currentStep: "",
        progressMessage: ""
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
    }
  },

  updateSolution: async (solutionId: string, updates: Partial<Solution>) => {
    try {
      const res = await apiClient.patch<Solution>(`/api/v1/solutions/${solutionId}`, updates);
      const updatedSolutions = get().solutions.map((sol) =>
        sol.id === solutionId ? res.data : sol
      );
      set({ solutions: updatedSolutions });
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || "Failed to update solution"
      });
      throw err;
    }
  },

  clearSolutions: () => {
    set({
      solutions: [],
      currentProblem: null,
      error: null,
      currentStep: "",
      progressMessage: ""
    });
  }
}));
