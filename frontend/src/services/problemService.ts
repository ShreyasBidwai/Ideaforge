import apiClient from "./api";
import type {
  ProblemStatement,
  PaginatedResponse,
} from "../types/api";

export const generateProblems = async (sessionId: string): Promise<ProblemStatement[]> => {
  const response = await apiClient.post<ProblemStatement[]>(
    `/api/v1/sessions/${sessionId}/generate-problems`
  );
  return response.data;
};

export const getProblems = async (filters?: {
  industry?: string | null;
  status?: string | null;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  per_page?: number;
}): Promise<PaginatedResponse<ProblemStatement>> => {
  const params: Record<string, any> = {};
  if (filters) {
    if (filters.industry) params.industry = filters.industry;
    if (filters.status) params.status = filters.status;
    if (filters.sort_by) params.sort_by = filters.sort_by;
    if (filters.sort_order) params.sort_order = filters.sort_order;
    if (filters.page) params.page = filters.page;
    if (filters.per_page) params.per_page = filters.per_page;
  }
  const response = await apiClient.get<PaginatedResponse<ProblemStatement>>(
    "/api/v1/problem-statements",
    { params }
  );
  return response.data;
};

export const getProblem = async (id: string): Promise<ProblemStatement> => {
  const response = await apiClient.get<ProblemStatement>(`/api/v1/problem-statements/${id}`);
  return response.data;
};

export const updateProblem = async (
  id: string,
  data: Partial<ProblemStatement>
): Promise<ProblemStatement> => {
  const response = await apiClient.patch<ProblemStatement>(
    `/api/v1/problem-statements/${id}`,
    data
  );
  return response.data;
};

export const selectProblem = async (id: string): Promise<ProblemStatement> => {
  const response = await apiClient.post<ProblemStatement>(
    `/api/v1/problem-statements/${id}/select`
  );
  return response.data;
};

export const archiveProblem = async (id: string): Promise<ProblemStatement> => {
  const response = await apiClient.delete<ProblemStatement>(
    `/api/v1/problem-statements/${id}`
  );
  return response.data;
};

export const getIndustries = async (): Promise<string[]> => {
  const response = await apiClient.get<string[]>(
    "/api/v1/problem-statements/industries"
  );
  return response.data;
};

export const problemService = {
  generateProblems,
  getProblems,
  getProblem,
  updateProblem,
  selectProblem,
  archiveProblem,
  getIndustries,
};

export default problemService;
