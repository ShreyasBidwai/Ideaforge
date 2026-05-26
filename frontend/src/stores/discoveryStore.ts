import { create } from "zustand";
import { type Session, type PainPoint, type ProblemStatement } from "../types/api";
import { sessionService } from "../services/sessionService";
import apiClient from "../services/api";

export interface MaturityLevelInfo {
  level: string;
  label: string;
  description: string;
}

interface DiscoveryState {
  currentSession: Session | null;
  painPoints: PainPoint[];
  isDiscovering: boolean;
  currentStep: string;
  error: string | null;
  selectedMaturity: string;
  selectedTechStack: string[];
  maturityLevels: MaturityLevelInfo[];
  generatedProblems: ProblemStatement[];
  isGeneratingProblems: boolean;
  createAndDiscover: (industry: string, location: string, maturityLevel: string, techStack: string[]) => Promise<void>;
  clearSession: () => void;
  fetchMaturityLevels: () => Promise<void>;
  setSelectedMaturity: (maturity: string) => void;
  setSelectedTechStack: (techStack: string[]) => void;
  generateProblems: (sessionId: string) => Promise<void>;
}

export const useDiscoveryStore = create<DiscoveryState>((set, get) => ({
  currentSession: null,
  painPoints: [],
  isDiscovering: false,
  currentStep: "",
  error: null,
  selectedMaturity: "mvp",
  selectedTechStack: [],
  maturityLevels: [],
  generatedProblems: [],
  isGeneratingProblems: false,

  createAndDiscover: async (industry: string, location: string, maturityLevel: string, techStack: string[]) => {
    set({ isDiscovering: true, error: null, painPoints: [], currentStep: "starting" });
    try {
      const session = await sessionService.createSession({
        industry,
        location,
        maturity_level: maturityLevel as any,
        tech_stack_preferences: techStack,
      });
      set({ currentSession: session });

      const { streamDiscover } = await import("../services/streamService");

      await streamDiscover(
        session.id,
        (status, message) => {
          set({ currentStep: status });
        },
        (pps) => {
          const updatedSession: Session = {
            ...session,
            pain_points: pps,
            status: "problem_generation",
          };
          set({
            currentSession: updatedSession,
            painPoints: pps,
            isDiscovering: false,
            currentStep: "complete",
          });
        },
        (err) => {
          set({
            isDiscovering: false,
            error: err,
            currentStep: "",
          });
        }
      );
    } catch (error: any) {
      const errMsg = error?.response?.data?.detail || error?.message || "Failed to discover pain points";
      set({
        isDiscovering: false,
        error: errMsg,
        currentStep: "",
      });
      throw error;
    }
  },

  clearSession: () => {
    set({
      currentSession: null,
      painPoints: [],
      isDiscovering: false,
      currentStep: "",
      error: null,
      generatedProblems: [],
      isGeneratingProblems: false,
    });
  },

  fetchMaturityLevels: async () => {
    try {
      const response = await apiClient.get<MaturityLevelInfo[]>("/api/v1/maturity-levels");
      set({ maturityLevels: response.data || [] });
    } catch (error) {
      console.error("Failed to fetch maturity levels:", error);
    }
  },

  setSelectedMaturity: (maturity: string) => {
    set({ selectedMaturity: maturity });
  },

  setSelectedTechStack: (techStack: string[]) => {
    set({ selectedTechStack: techStack });
  },

  generateProblems: async (sessionId: string) => {
    set({ isGeneratingProblems: true, error: null, currentStep: "starting" });
    try {
      const { streamProblems } = await import("../services/streamService");
      
      await streamProblems(
        sessionId,
        (status, message) => {
          set({ currentStep: status });
        },
        (problems) => {
          set((state) => ({
            generatedProblems: problems,
            isGeneratingProblems: false,
            currentStep: "complete",
            currentSession: state.currentSession
              ? { ...state.currentSession, status: "solution_generation" }
              : null,
          }));
        },
        (err) => {
          set({
            isGeneratingProblems: false,
            error: err,
            currentStep: "",
          });
        }
      );
    } catch (error: any) {
      const errMsg = error?.response?.data?.detail || error?.message || "Failed to generate problem statements";
      set({
        isGeneratingProblems: false,
        error: errMsg,
        currentStep: "",
      });
      throw error;
    }
  },
}));
