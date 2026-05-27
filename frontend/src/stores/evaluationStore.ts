import { create } from 'zustand';
import evaluationService from '../services/evaluationService';
import { problemService } from '../services/problemService';
import { sessionService } from '../services/sessionService';
import type { Rubric, DisqualifierResult, ScoringResult, AttackResult, ACHResult, ComparisonResult } from '../types/api';

export interface EvaluationState {
  currentStep: 'rubric' | 'disqualifiers' | 'scoring' | 'attacks' | 'ach' | 'comparison';
  rubric: Rubric | null;
  isRubricLocked: boolean;
  disqualifierResults: DisqualifierResult[] | null;
  scores: ScoringResult[] | null;
  attacks: AttackResult[] | null;
  achAnalysis: ACHResult[] | null;
  comparison: ComparisonResult | null;
  isLoading: boolean;
  maturitySteps: string[];
  
  generateRubric: (problemId: string) => Promise<void>;
  updateRubric: (problemId: string, rubric: Rubric) => Promise<void>;
  lockRubric: (problemId: string) => Promise<void>;
  runDisqualifiers: (problemId: string) => Promise<void>;
  runScoring: (problemId: string) => Promise<void>;
  runAttacks: (problemId: string) => Promise<void>;
  runACH: (problemId: string) => Promise<void>;
  generateComparison: (problemId: string) => Promise<void>;
  loadFullEvaluation: (problemId: string) => Promise<void>;
  setStep: (step: 'rubric' | 'disqualifiers' | 'scoring' | 'attacks' | 'ach' | 'comparison') => void;
}

export const useEvaluationStore = create<EvaluationState>((set) => ({
  currentStep: 'rubric',
  rubric: null,
  isRubricLocked: false,
  disqualifierResults: null,
  scores: null,
  attacks: null,
  achAnalysis: null,
  comparison: null,
  isLoading: false,
  maturitySteps: ['rubric', 'disqualifiers', 'scoring', 'attacks', 'ach', 'comparison'],

  generateRubric: async (problemId) => {
    set({ isLoading: true });
    try {
      const res = await evaluationService.generateRubric(problemId);
      set({ rubric: res.rubric, isRubricLocked: res.is_locked });
    } finally {
      set({ isLoading: false });
    }
  },

  updateRubric: async (problemId, rubric) => {
    set({ isLoading: true });
    try {
      const res = await evaluationService.updateRubric(problemId, rubric);
      set({ rubric: res.rubric, isRubricLocked: res.is_locked });
    } finally {
      set({ isLoading: false });
    }
  },

  lockRubric: async (problemId) => {
    set({ isLoading: true });
    try {
      const res = await evaluationService.lockRubric(problemId);
      set({ rubric: res.rubric, isRubricLocked: res.is_locked });
    } finally {
      set({ isLoading: false });
    }
  },

  runDisqualifiers: async (problemId) => {
    set({ isLoading: true });
    try {
      const res = await evaluationService.runDisqualifiers(problemId);
      set({ disqualifierResults: res.results });
    } finally {
      set({ isLoading: false });
    }
  },

  runScoring: async (problemId) => {
    set({ isLoading: true });
    try {
      const res = await evaluationService.runScoring(problemId);
      set({ scores: res.scores });
    } finally {
      set({ isLoading: false });
    }
  },

  runAttacks: async (problemId) => {
    set({ isLoading: true });
    try {
      const res = await evaluationService.runAttacks(problemId);
      set({ attacks: res.attacks });
    } finally {
      set({ isLoading: false });
    }
  },

  runACH: async (problemId) => {
    set({ isLoading: true });
    try {
      const res = await evaluationService.runACH(problemId);
      set({ achAnalysis: res.analysis });
    } finally {
      set({ isLoading: false });
    }
  },

  generateComparison: async (problemId) => {
    set({ isLoading: true });
    try {
      const res = await evaluationService.generateComparison(problemId);
      set({ comparison: res });
    } finally {
      set({ isLoading: false });
    }
  },

  loadFullEvaluation: async (problemId) => {
    set({ isLoading: true });
    try {
      const problem = await problemService.getProblem(problemId);
      const session = await sessionService.getSession(problem.session_id);
      
      const steps = ['rubric', 'disqualifiers', 'scoring'];
      if (session.maturity_level !== 'poc') {
        steps.push('attacks', 'ach');
      }
      steps.push('comparison');
      
      set({ maturitySteps: steps });

      const state = await evaluationService.getFullEvaluation(problemId);
      
      set({
        rubric: state.rubric || null,
        isRubricLocked: state.status !== 'pending' && state.status !== undefined,
        disqualifierResults: state.disqualifier_results?.results || null,
        scores: state.scores?.scores || null,
        attacks: state.attacks?.attacks || null,
        achAnalysis: state.ach_analysis?.analysis || null,
        comparison: state.comparison || null,
      });
    } catch (e) {
      console.error(e);
    } finally {
      set({ isLoading: false });
    }
  },

  setStep: (step) => {
    set({ currentStep: step });
  }
}));
