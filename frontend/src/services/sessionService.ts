import apiClient from "./api";
import type {
  Session,
  CreateSessionRequest,
  PainPoint,
} from "../types/api";

export const createSession = async (data: CreateSessionRequest): Promise<Session> => {
  const response = await apiClient.post<Session>("/api/v1/sessions", data);
  return response.data;
};

export const getSession = async (id: string): Promise<Session> => {
  const response = await apiClient.get<Session>(`/api/v1/sessions/${id}`);
  return response.data;
};

export const getUserSessions = async (): Promise<Session[]> => {
  const response = await apiClient.get<any>("/api/v1/sessions");
  if (response.data && Array.isArray(response.data.items)) {
    return response.data.items;
  }
  if (Array.isArray(response.data)) {
    return response.data;
  }
  return [];
};

export const discoverPainPoints = async (sessionId: string): Promise<PainPoint[]> => {
  const response = await apiClient.post<any>(`/api/v1/sessions/${sessionId}/discover`);
  if (response.data && Array.isArray(response.data.pain_points)) {
    return response.data.pain_points;
  }
  if (Array.isArray(response.data)) {
    return response.data;
  }
  return [];
};

export const sessionService = {
  createSession,
  getSession,
  getUserSessions,
  discoverPainPoints,
};

export default sessionService;
