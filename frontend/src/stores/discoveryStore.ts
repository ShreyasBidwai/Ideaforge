import { create } from "zustand";
import { type Session, type PainPoint } from "../types/api";
import { sessionService } from "../services/sessionService";

interface DiscoveryState {
  currentSession: Session | null;
  painPoints: PainPoint[];
  isDiscovering: boolean;
  error: string | null;
  createAndDiscover: (industry: string, location: string, maturityLevel: string, techStack: string[]) => Promise<void>;
  clearSession: () => void;
}

export const useDiscoveryStore = create<DiscoveryState>((set) => ({
  currentSession: null,
  painPoints: [],
  isDiscovering: false,
  error: null,

  createAndDiscover: async (industry: string, location: string, maturityLevel: string, techStack: string[]) => {
    set({ isDiscovering: true, error: null, painPoints: [] });
    try {
      const session = await sessionService.createSession({
        industry,
        location,
        maturity_level: maturityLevel as any,
        tech_stack_preferences: techStack,
      });
      set({ currentSession: session });

      const painPoints = await sessionService.discoverPainPoints(session.id);

      const updatedSession: Session = {
        ...session,
        pain_points: painPoints,
        status: "problem_generation",
      };

      set({
        currentSession: updatedSession,
        painPoints,
        isDiscovering: false,
      });
    } catch (error: any) {
      const errMsg = error?.response?.data?.detail || error?.message || "Failed to discover pain points";
      set({
        isDiscovering: false,
        error: errMsg,
      });
      throw error;
    }
  },

  clearSession: () => {
    set({
      currentSession: null,
      painPoints: [],
      isDiscovering: false,
      error: null,
    });
  },
}));
