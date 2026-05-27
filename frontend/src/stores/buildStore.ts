import { create } from "zustand";
import type { Project, Sprint, SprintTask, BuildLogEntry } from "../types/api";
import apiClient from "../services/api";
import { useAuthStore } from "./authStore";

interface BuildState {
  project: Project | null;
  sprints: Sprint[];
  logs: BuildLogEntry[];
  status: string;
  currentTask: SprintTask | null;
  stats: { completedTasks: number; totalTasks: number; testsPassing: number; eta: string; };
  rateLimitInfo: { isLimited: boolean; resumeAt: string | null; usage: number; capacity: number; } | null;
  isConnected: boolean;
  
  fetchBuildStatus: (projectId: string) => Promise<void>;
  startBuild: (projectId: string) => Promise<void>;
  pauseBuild: (projectId: string) => Promise<void>;
  cancelBuild: (projectId: string) => Promise<void>;
  connectLogStream: (projectId: string) => void;
  disconnectLogStream: () => void;
}

export const useBuildStore = create<BuildState>((set, get) => ({
  project: null,
  sprints: [],
  logs: [],
  status: "pending",
  currentTask: null,
  stats: { completedTasks: 0, totalTasks: 0, testsPassing: 0, eta: "--" },
  rateLimitInfo: null,
  isConnected: false,

  fetchBuildStatus: async (projectId) => {
    try {
      const [projectRes, sprintsRes, statusRes, logsRes] = await Promise.all([
        apiClient.get(`/api/v1/projects/${projectId}`),
        apiClient.get(`/api/v1/projects/${projectId}/sprints`),
        apiClient.get(`/api/v1/projects/${projectId}/build/status`),
        apiClient.get(`/api/v1/projects/${projectId}/build/logs`),
      ]);

      const project = projectRes.data;
      const sprints = sprintsRes.data;
      const statusData = statusRes.data;
      const logs = logsRes.data;

      const totalTasks = statusData.total_tasks || 0;
      const completedTasks = statusData.passed_tasks || 0;
      
      let testsPassing = 0;
      sprints.forEach((sprint: any) => {
        sprint.tasks?.forEach((task: any) => {
          testsPassing += task.tests_passed || 0;
        });
      });

      const eta = statusData.status === "building" ? `~${Math.ceil((totalTasks - completedTasks) * 5)}m` : "--";

      const currentTask = statusData.current_task;
      const isLimited = statusData.status === "rate_limited";
      const resumeAt = isLimited && currentTask?.rate_limit_reset_at 
        ? new Date(currentTask.rate_limit_reset_at).toLocaleTimeString() 
        : null;

      const usage = isLimited ? 30 : Math.min(23, completedTasks + 5);

      set({
        project,
        sprints,
        logs,
        status: statusData.status,
        currentTask,
        stats: { completedTasks, totalTasks, testsPassing, eta },
        rateLimitInfo: {
          isLimited,
          resumeAt,
          usage,
          capacity: 30
        }
      });
    } catch (error) {
      console.error("Error fetching build status:", error);
    }
  },

  startBuild: async (projectId) => {
    try {
      const res = await apiClient.post(`/api/v1/projects/${projectId}/build/start`);
      set({ status: res.data.status });
    } catch (error) {
      console.error("Error starting build:", error);
    }
  },

  pauseBuild: async (projectId) => {
    try {
      const res = await apiClient.post(`/api/v1/projects/${projectId}/build/pause`);
      set({ status: res.data.status });
    } catch (error) {
      console.error("Error pausing build:", error);
    }
  },

  cancelBuild: async (projectId) => {
    try {
      const res = await apiClient.post(`/api/v1/projects/${projectId}/build/cancel`);
      set({ status: res.data.status });
    } catch (error) {
      console.error("Error cancelling build:", error);
    }
  },

  connectLogStream: (projectId) => {
    if (get().isConnected) return;
    
    const token = typeof useAuthStore.getState === "function" ? useAuthStore.getState().accessToken : undefined;
    const controller = new AbortController();
    
    (window as any)._buildLogAbortController = controller;
    set({ isConnected: true });

    const fetchLogsStream = async () => {
      try {
        const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
        const response = await fetch(`${baseUrl}/api/v1/projects/${projectId}/build/logs`, {
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
            if (line.trim().startsWith("data: ")) {
              try {
                const eventData = JSON.parse(line.trim().slice(6));
                set((state) => {
                  if (state.logs.some((l) => l.id === eventData.id)) {
                    return state;
                  }
                  return { logs: [...state.logs, eventData] };
                });
              } catch (e) {
                // Ignore
              }
            }
          }
        }
      } catch (err: any) {
        if (err.name !== "AbortError") {
          console.error("Log stream error:", err);
          set({ isConnected: false });
          setTimeout(() => {
            if (get().project && !get().isConnected) {
              get().connectLogStream(projectId);
            }
          }, 3000);
        }
      }
    };

    fetchLogsStream();
  },

  disconnectLogStream: () => {
    const controller = (window as any)._buildLogAbortController;
    if (controller) {
      controller.abort();
      (window as any)._buildLogAbortController = null;
    }
    set({ isConnected: false });
  }
}));
