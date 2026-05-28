import { create } from "zustand";
import apiClient from "../services/api";
import { useAuthStore } from "./authStore";

export interface SetupStep {
  id: string;
  project_id: string;
  step_type: "api_key" | "env_var" | "external_account" | "oauth_config" | "system_install" | "manual_action";
  title: string;
  description: string;
  target_file?: string;
  env_key?: string;
  is_required: boolean;
  is_completed: boolean;
  doc_url?: string;
  created_at: string;
}

interface RunState {
  setupSteps: SetupStep[];
  ready: boolean;
  installStatus: "stopped" | "installing" | "installed" | "install_failed";
  runStatus: "stopped" | "running" | "error" | "starting" | "installing";
  backendUrl: string | null;
  frontendUrl: string | null;
  backendLogs: string[];
  frontendLogs: string[];
  installLogs: string[];

  fetchManifest: (projectId: string) => Promise<void>;
  saveEnvValue: (projectId: string, stepId: string, value: string) => Promise<void>;
  markStep: (projectId: string, stepId: string, completed: boolean) => Promise<void>;
  install: (projectId: string) => Promise<void>;
  start: (projectId: string) => Promise<void>;
  stop: (projectId: string) => Promise<void>;
  connectLogs: (projectId: string, source: "backend" | "frontend" | "install") => void;
  disconnectLogs: (source: "backend" | "frontend" | "install") => void;
}

const abortControllers: Record<string, AbortController> = {};

export const useRunStore = create<RunState>((set, get) => ({
  setupSteps: [],
  ready: false,
  installStatus: "stopped",
  runStatus: "stopped",
  backendUrl: null,
  frontendUrl: null,
  backendLogs: [],
  frontendLogs: [],
  installLogs: [],

  fetchManifest: async (projectId) => {
    try {
      const res = await apiClient.get(`/api/v1/projects/${projectId}/setup-manifest`);
      const steps = res.data;
      set({ setupSteps: steps });

      // Fetch readiness status
      const readyRes = await apiClient.get(`/api/v1/projects/${projectId}/setup-manifest/ready`);
      set({ ready: !!readyRes.data.ready });

      // Also get run/install status
      const statusRes = await apiClient.get(`/api/v1/projects/${projectId}/run/status`);
      const data = statusRes.data;
      set({
        runStatus: data.status,
        backendUrl: data.backend_url,
        frontendUrl: data.frontend_url,
        installStatus: data.status === "installing" ? "installing" : get().installStatus
      });
    } catch (e) {
      console.error("Error fetching manifest:", e);
    }
  },

  saveEnvValue: async (projectId, stepId, value) => {
    try {
      await apiClient.post(`/api/v1/projects/${projectId}/setup-steps/${stepId}/value`, { value });
      await get().fetchManifest(projectId);
    } catch (e) {
      console.error("Error saving env value:", e);
      throw e;
    }
  },

  markStep: async (projectId, stepId, completed) => {
    try {
      await apiClient.patch(`/api/v1/projects/${projectId}/setup-steps/${stepId}`, { is_completed: completed });
      await get().fetchManifest(projectId);
    } catch (e) {
      console.error("Error marking step:", e);
      throw e;
    }
  },

  install: async (projectId) => {
    set({ installStatus: "installing", installLogs: [] });
    // Connect install logs stream
    get().connectLogs(projectId, "install");

    try {
      const res = await apiClient.post(`/api/v1/projects/${projectId}/run/install`);
      if (res.data.success) {
        set({ installStatus: "installed" });
      } else {
        set({ installStatus: "install_failed" });
      }
    } catch (e) {
      set({ installStatus: "install_failed" });
      console.error("Error installing project dependencies:", e);
    } finally {
      // Allow a brief delay for final logs to stream, then disconnect
      setTimeout(() => {
        get().disconnectLogs("install");
      }, 1000);
    }
  },

  start: async (projectId) => {
    set({ runStatus: "starting", backendLogs: [], frontendLogs: [] });
    try {
      const res = await apiClient.post(`/api/v1/projects/${projectId}/run/start`);
      set({
        runStatus: res.data.status,
        backendUrl: res.data.backend_url,
        frontendUrl: res.data.frontend_url
      });
    } catch (e) {
      set({ runStatus: "error" });
      console.error("Error starting project:", e);
      throw e;
    }
  },

  stop: async (projectId) => {
    try {
      const res = await apiClient.post(`/api/v1/projects/${projectId}/run/stop`);
      set({
        runStatus: res.data.status,
        backendUrl: null,
        frontendUrl: null
      });
    } catch (e) {
      console.error("Error stopping project:", e);
      throw e;
    }
  },

  connectLogs: (projectId, source) => {
    // If already connected for this source, disconnect first
    if (abortControllers[source]) {
      get().disconnectLogs(source);
    }

    const token = typeof useAuthStore.getState === "function" ? useAuthStore.getState().accessToken : undefined;
    const controller = new AbortController();
    abortControllers[source] = controller;

    const fetchLogsStream = async () => {
      try {
        const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
        const response = await fetch(`${baseUrl}/api/v1/projects/${projectId}/run/logs/stream?source=${source}`, {
          headers: {
            "Accept": "text/event-stream",
            "Authorization": `Bearer ${token}`
          },
          signal: controller.signal
        });

        if (!response.ok) {
          throw new Error("HTTP error on log stream connection");
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        if (!reader) return;

        let buffer = "";
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith("data: ")) {
              try {
                const eventData = JSON.parse(trimmed.slice(6));
                set((state) => {
                  if (source === "backend") {
                    return { backendLogs: [...state.backendLogs, eventData] };
                  } else if (source === "frontend") {
                    return { frontendLogs: [...state.frontendLogs, eventData] };
                  } else {
                    return { installLogs: [...state.installLogs, eventData] };
                  }
                });
              } catch (e) {
                // Not JSON (could be a simple text line)
                const textLine = trimmed.slice(6);
                set((state) => {
                  if (source === "backend") {
                    return { backendLogs: [...state.backendLogs, textLine] };
                  } else if (source === "frontend") {
                    return { frontendLogs: [...state.frontendLogs, textLine] };
                  } else {
                    return { installLogs: [...state.installLogs, textLine] };
                  }
                });
              }
            }
          }
        }
      } catch (err: any) {
        if (err.name !== "AbortError") {
          console.error(`Log stream connection error for ${source}:`, err);
        }
      }
    };

    fetchLogsStream();
  },

  disconnectLogs: (source) => {
    const controller = abortControllers[source];
    if (controller) {
      controller.abort();
      delete abortControllers[source];
    }
  }
}));
