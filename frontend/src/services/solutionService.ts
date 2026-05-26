import apiClient from "./api";
import type { Solution } from "../types/api";

export const generateSolutions = async (problemId: string): Promise<Solution[]> => {
  const response = await apiClient.post<Solution[]>(
    `/api/v1/solutions/generate`,
    null,
    { params: { problem_id: problemId } }
  );
  return response.data;
};

export const getSolutions = async (problemId: string): Promise<Solution[]> => {
  const response = await apiClient.get<Solution[]>("/api/v1/solutions/", {
    params: { problem_id: problemId },
  });
  return response.data;
};

export const getSolution = async (id: string): Promise<Solution> => {
  const response = await apiClient.get<Solution>(`/api/v1/solutions/${id}`);
  return response.data;
};

export const approveSolution = async (id: string): Promise<Solution> => {
  const response = await apiClient.post<Solution>(`/api/v1/solutions/${id}/approve`);
  return response.data;
};

export const solutionService = {
  generateSolutions,
  getSolutions,
  getSolution,
  approveSolution,
};

export default solutionService;
