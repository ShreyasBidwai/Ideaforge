import apiClient from "./api";
import type { Evaluation, Rubric } from "../types/api";

export const runEvaluation = async (solutionIds: string[]): Promise<Evaluation[]> => {
  const response = await apiClient.post<Evaluation[]>(
    "/api/v1/evaluations/run",
    { solution_ids: solutionIds }
  );
  return response.data;
};

export const getEvaluation = async (id: string): Promise<Evaluation> => {
  const response = await apiClient.get<Evaluation>(`/api/v1/evaluations/${id}`);
  return response.data;
};

export const updateRubric = async (
  evaluationId: string,
  rubric: Rubric
): Promise<Evaluation> => {
  const response = await apiClient.put<Evaluation>(
    `/api/v1/evaluations/${evaluationId}/rubric`,
    rubric
  );
  return response.data;
};

export const evaluationService = {
  runEvaluation,
  getEvaluation,
  updateRubric,
};

export default evaluationService;
