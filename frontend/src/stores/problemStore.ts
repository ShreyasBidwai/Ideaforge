import { create } from "zustand";
import { type ProblemStatement } from "../types/api";
import { problemService } from "../services/problemService";

export interface ProblemState {
  problems: ProblemStatement[];
  total: number;
  page: number;
  filters: {
    industry: string | null;
    status: string | null;
    sortBy: string;
    sortOrder: string;
    search: string;
  };
  industries: string[];
  isLoading: boolean;
  fetchProblems: () => Promise<void>;
  fetchIndustries: () => Promise<void>;
  setFilters: (filters: Partial<ProblemState["filters"]>) => void;
  setPage: (page: number) => void;
  selectProblem: (id: string) => Promise<void>;
  archiveProblem: (id: string) => Promise<void>;
}

export const useProblemStore = create<ProblemState>((set, get) => ({
  problems: [],
  total: 0,
  page: 1,
  filters: {
    industry: null,
    status: null,
    sortBy: "overall_rating",
    sortOrder: "desc",
    search: "",
  },
  industries: [],
  isLoading: false,

  fetchProblems: async () => {
    set({ isLoading: true });
    try {
      const { filters, page } = get();
      const res = await problemService.getProblems({
        industry: filters.industry,
        status: filters.status,
        sort_by: filters.sortBy,
        sort_order: filters.sortOrder,
        page,
        per_page: 20,
      });
      set({ problems: res.items || [], total: res.total || 0 });
    } catch (err) {
      console.error("Failed to fetch problems:", err);
    } finally {
      set({ isLoading: false });
    }
  },

  fetchIndustries: async () => {
    try {
      const industries = await problemService.getIndustries();
      set({ industries });
    } catch (err) {
      console.error("Failed to fetch industries:", err);
    }
  },

  setFilters: (newFilters) => {
    set((state) => ({
      filters: { ...state.filters, ...newFilters },
      page: 1,
    }));
    get().fetchProblems();
  },

  setPage: (page) => {
    set({ page });
    get().fetchProblems();
  },

  selectProblem: async (id) => {
    try {
      await problemService.selectProblem(id);
      await get().fetchProblems();
    } catch (err) {
      console.error("Failed to select problem:", err);
    }
  },

  archiveProblem: async (id) => {
    try {
      await problemService.archiveProblem(id);
      await get().fetchProblems();
    } catch (err) {
      console.error("Failed to archive problem:", err);
    }
  },
}));
