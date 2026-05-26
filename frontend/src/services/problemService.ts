import apiClient from "./api";
import type {
  ProblemStatement,
  PaginatedResponse,
} from "../types/api";

export const generateProblems = async (sessionId: string): Promise<ProblemStatement[]> => {
  const response = await apiClient.post<ProblemStatement[]>(
    `/api/v1/problems/generate`,
    null,
    { params: { session_id: sessionId } }
  );
  return response.data;
};

export const getProblems = async (filters?: {
  industry?: string;
  status?: string;
  page?: number;
  per_page?: number;
}): Promise<PaginatedResponse<ProblemStatement>> => {
  const response = await apiClient.get<PaginatedResponse<ProblemStatement>>(
    "/api/v1/problems/",
    { params: filters }
  );
  return response.data;
};

export const getProblem = async (id: string): Promise<ProblemStatement> => {
  const response = await apiClient.get<ProblemStatement>(`/api/v1/problems/${id}`);
  return response.data;
};

export const updateProblem = async (
  id: string,
  data: Partial<ProblemStatement>
): Promise<ProblemStatement> => {
  const response = await apiClient.patch<ProblemStatement>(
    `/api/v1/problems/${id}`,
    data
  );
  return response.data;
};

export const problemService = {
  generateProblems,
  getProblems,
  getProblem,
  updateProblem,
};

export default problemService;
