import apiClient from "./api";
import type {
  LoginRequest,
  TokenResponse,
  RegisterRequest,
  User,
} from "../types/api";

export const authService = {
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>("/api/v1/auth/login", data);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<User> => {
    const response = await apiClient.post<User>("/api/v1/auth/register", data);
    return response.data;
  },

  refreshToken: async (token: string): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>("/api/v1/auth/refresh", {
      refresh_token: token,
    });
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>("/api/v1/auth/me");
    return response.data;
  },
};

export default authService;
