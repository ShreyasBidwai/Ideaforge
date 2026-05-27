import apiClient from "./api";
import type { Rubric, DisqualifierResult, ScoringResult, AttackResult, ACHResult, ComparisonResult } from "../types/api";

export const generateRubric = async (problemId: string): Promise<{ rubric: Rubric; is_locked: boolean }> => {
  const response = await apiClient.post<{ rubric: Rubric; is_locked: boolean }>(
    `/api/v1/problem-statements/${problemId}/evaluation/rubric`
  );
  return response.data;
};

export const getRubric = async (problemId: string): Promise<{ rubric: Rubric; is_locked: boolean }> => {
  const response = await apiClient.get<{ rubric: Rubric; is_locked: boolean }>(
    `/api/v1/problem-statements/${problemId}/evaluation/rubric`
  );
  return response.data;
};

export const updateRubric = async (problemId: string, rubric: Rubric): Promise<{ rubric: Rubric; is_locked: boolean }> => {
  const response = await apiClient.patch<{ rubric: Rubric; is_locked: boolean }>(
    `/api/v1/problem-statements/${problemId}/evaluation/rubric`,
    rubric
  );
  return response.data;
};

export const lockRubric = async (problemId: string): Promise<{ rubric: Rubric; is_locked: boolean }> => {
  const response = await apiClient.post<{ rubric: Rubric; is_locked: boolean }>(
    `/api/v1/problem-statements/${problemId}/evaluation/rubric/lock`
  );
  return response.data;
};

export const runDisqualifiers = async (problemId: string): Promise<{ results: DisqualifierResult[] }> => {
  const response = await apiClient.post<{ results: DisqualifierResult[] }>(
    `/api/v1/problem-statements/${problemId}/evaluation/disqualify`
  );
  return response.data;
};

export const runScoring = async (problemId: string): Promise<{ scores: ScoringResult[] }> => {
  const response = await apiClient.post<{ scores: ScoringResult[] }>(
    `/api/v1/problem-statements/${problemId}/evaluation/score`
  );
  return response.data;
};

export const runAttacks = async (problemId: string): Promise<{ attacks: AttackResult[] }> => {
  const response = await apiClient.post<{ attacks: AttackResult[] }>(
    `/api/v1/problem-statements/${problemId}/evaluation/attack`
  );
  return response.data;
};

export const runACH = async (problemId: string): Promise<{ analysis: ACHResult[] }> => {
  const response = await apiClient.post<{ analysis: ACHResult[] }>(
    `/api/v1/problem-statements/${problemId}/evaluation/ach`
  );
  return response.data;
};

export const generateComparison = async (problemId: string): Promise<ComparisonResult> => {
  const response = await apiClient.post<ComparisonResult>(
    `/api/v1/problem-statements/${problemId}/evaluation/compare`
  );
  return response.data;
};

export const getFullEvaluation = async (problemId: string): Promise<any> => {
  const response = await apiClient.get<any>(
    `/api/v1/problem-statements/${problemId}/evaluation`
  );
  return response.data;
};

// Backward-compatibility exports for Sprint 1 tests
export const runEvaluation = async (solutionIds: string[]): Promise<any[]> => {
  const response = await apiClient.post<any[]>(
    "/api/v1/evaluations/run",
    { solution_ids: solutionIds }
  );
  return response.data;
};

export const getEvaluation = async (id: string): Promise<any> => {
  const response = await apiClient.get<any>(`/api/v1/evaluations/${id}`);
  return response.data;
};

export const evaluationService = {
  generateRubric,
  getRubric,
  updateRubric,
  lockRubric,
  runDisqualifiers,
  runScoring,
  runAttacks,
  runACH,
  generateComparison,
  getFullEvaluation,
  runEvaluation,
  getEvaluation
};

export default evaluationService;
