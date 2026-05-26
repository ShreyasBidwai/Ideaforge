import apiClient from "./api";
import type {
  ProblemStatement,
  PaginatedResponse,
} from "../types/api";

export const problemService = {
  generateProblems: async (sessionId: string): Promise<ProblemStatement[]> => {
    const response = await apiClient.post<ProblemStatement[]>(
      `/api/v1/problems/generate`,
      null,
      { params: { session_id: sessionId } }
    );
    return response.data;
  },

  getProblems: async (filters?: {
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
  },

  getProblem: async (id: string): Promise<ProblemStatement> => {
    const response = await apiClient.get<ProblemStatement>(`/api/v1/problems/${id}`);
    return response.data;
  },

  updateProblem: async (
    id: string,
    data: Partial<ProblemStatement>
  ): Promise<ProblemStatement> => {
    const response = await apiClient.patch<ProblemStatement>(
      `/api/v1/problems/${id}`,
      data
    );
    return response.data;
  },
};

export default problemService;
