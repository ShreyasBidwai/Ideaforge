import { useAuthStore } from "../stores/authStore";
import type { PainPoint, ProblemStatement, Solution } from "../types/api";

export async function streamDiscover(
  sessionId: string,
  onProgress: (status: string, message: string) => void,
  onComplete: (painPoints: PainPoint[]) => void,
  onError: (error: string) => void
): Promise<void> {
  const token = useAuthStore.getState().accessToken;
  const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const url = `${baseUrl}/api/v1/sessions/${sessionId}/discover/stream`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => "Unknown error");
      throw new Error(`Streaming failed: ${response.status} - ${errorText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("Response body is not readable");
    }

    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() || "";

      for (const block of blocks) {
        if (!block.trim()) continue;

        let currentEvent = "";
        let currentData = "";

        const lines = block.split("\n");
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.substring(7).trim();
          } else if (line.startsWith("data: ")) {
            currentData = line.substring(6).trim();
          }
        }

        if (currentData) {
          try {
            const parsedData = JSON.parse(currentData);
            if (currentEvent === "progress") {
              onProgress(parsedData.status || "", parsedData.message || "");
            } else if (currentEvent === "complete") {
              const pps = parsedData.data?.pain_points || [];
              onComplete(pps);
            } else if (currentEvent === "error") {
              onError(parsedData.message || "An error occurred during discovery");
            }
          } catch (e) {
            console.error("Failed to parse SSE data JSON", e);
          }
        }
      }
    }
  } catch (error: any) {
    onError(error.message || "Network error");
  }
}

export async function streamProblems(
  sessionId: string,
  onProgress: (status: string, message: string) => void,
  onComplete: (problems: ProblemStatement[]) => void,
  onError: (error: string) => void
): Promise<void> {
  const token = useAuthStore.getState().accessToken;
  const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const url = `${baseUrl}/api/v1/sessions/${sessionId}/generate-problems/stream`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => "Unknown error");
      throw new Error(`Streaming failed: ${response.status} - ${errorText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("Response body is not readable");
    }

    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() || "";

      for (const block of blocks) {
        if (!block.trim()) continue;

        let currentEvent = "";
        let currentData = "";

        const lines = block.split("\n");
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.substring(7).trim();
          } else if (line.startsWith("data: ")) {
            currentData = line.substring(6).trim();
          }
        }

        if (currentData) {
          try {
            const parsedData = JSON.parse(currentData);
            if (currentEvent === "progress") {
              onProgress(parsedData.status || "", parsedData.message || "");
            } else if (currentEvent === "complete") {
              const problems = parsedData.data || [];
              onComplete(problems);
            } else if (currentEvent === "error") {
              onError(parsedData.message || "An error occurred during problem statement generation");
            }
          } catch (e) {
            console.error("Failed to parse SSE data JSON", e);
          }
        }
      }
    }
  } catch (error: any) {
    onError(error.message || "Network error");
  }
}

export async function streamSolutions(
  problemId: string,
  onProgress: (status: string, message: string) => void,
  onComplete: (solutions: Solution[]) => void,
  onError: (error: string) => void
): Promise<void> {
  const token = useAuthStore.getState().accessToken;
  const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const url = `${baseUrl}/api/v1/problem-statements/${problemId}/generate-solutions/stream`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => "Unknown error");
      throw new Error(`Streaming failed: ${response.status} - ${errorText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("Response body is not readable");
    }

    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() || "";

      for (const block of blocks) {
        if (!block.trim()) continue;

        let currentEvent = "";
        let currentData = "";

        const lines = block.split("\n");
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.substring(7).trim();
          } else if (line.startsWith("data: ")) {
            currentData = line.substring(6).trim();
          }
        }

        if (currentData) {
          try {
            const parsedData = JSON.parse(currentData);
            if (currentEvent === "progress") {
              onProgress(parsedData.status || "", parsedData.message || "");
            } else if (currentEvent === "complete") {
              const solutions = parsedData.data || [];
              onComplete(solutions);
            } else if (currentEvent === "error") {
              onError(parsedData.message || "An error occurred during solution generation");
            }
          } catch (e) {
            console.error("Failed to parse SSE data JSON", e);
          }
        }
      }
    }
  } catch (error: any) {
    onError(error.message || "Network error");
  }
}

