import apiClient from "./api";
import type {
  Session,
  CreateSessionRequest,
  PainPoint,
} from "../types/api";

export const sessionService = {
  createSession: async (data: CreateSessionRequest): Promise<Session> => {
    const response = await apiClient.post<Session>("/api/v1/sessions/", data);
    return response.data;
  },

  getSession: async (id: string): Promise<Session> => {
    const response = await apiClient.get<Session>(`/api/v1/sessions/${id}`);
    return response.data;
  },

  getUserSessions: async (): Promise<Session[]> => {
    const response = await apiClient.get<Session[]>("/api/v1/sessions/");
    return response.data;
  },

  discoverPainPoints: async (sessionId: string): Promise<PainPoint[]> => {
    const response = await apiClient.post<PainPoint[]>(`/api/v1/sessions/${sessionId}/discover`);
    return response.data;
  },
};

export default sessionService;
