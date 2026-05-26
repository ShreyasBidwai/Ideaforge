import { create } from "zustand";
import { type User } from "../types/api";
import authService from "../services/authService";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  refreshAccessToken: (accessToken: string, refreshToken: string) => void;
  fetchCurrentUser: () => Promise<void>;
  setLoading: (isLoading: boolean) => void;
}

// Retrieve initial values from localStorage if present
const storedAccessToken = localStorage.getItem("access_token");
const storedRefreshToken = localStorage.getItem("refresh_token");
const storedUser = localStorage.getItem("user");

let initialUser: User | null = null;
if (storedUser) {
  try {
    initialUser = JSON.parse(storedUser);
  } catch (e) {
    // ignore
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  user: initialUser,
  accessToken: storedAccessToken,
  refreshToken: storedRefreshToken,
  isAuthenticated: !!storedAccessToken,
  isLoading: false,

  login: async (email, password) => {
    set({ isLoading: true });
    try {
      const tokens = await authService.login({ email, password });
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
      
      set({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        isAuthenticated: true,
      });

      const user = await authService.getCurrentUser();
      localStorage.setItem("user", JSON.stringify(user));
      
      set({ user, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  register: async (email, password, fullName) => {
    set({ isLoading: true });
    try {
      await authService.register({ email, password, full_name: fullName });
      
      // Auto login on success
      const tokens = await authService.login({ email, password });
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);

      set({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        isAuthenticated: true,
      });

      const user = await authService.getCurrentUser();
      localStorage.setItem("user", JSON.stringify(user));
      
      set({ user, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    set({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
    });
  },

  refreshAccessToken: (accessToken, refreshToken) => {
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
    set({ accessToken, refreshToken, isAuthenticated: true });
  },

  fetchCurrentUser: async () => {
    set({ isLoading: true });
    try {
      const user = await authService.getCurrentUser();
      localStorage.setItem("user", JSON.stringify(user));
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user");
      set({
        accessToken: null,
        refreshToken: null,
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
      throw error;
    }
  },

  setLoading: (isLoading) => set({ isLoading }),
}));
