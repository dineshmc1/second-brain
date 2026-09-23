import type { ChatResponse, Memory, StoredFile } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8765/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(body.detail ?? `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; mode: string; version: string }>("/health"),
  chat: (message: string, conversationId?: string, responseMode = "text") =>
    request<ChatResponse>("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, conversation_id: conversationId, response_mode: responseMode }),
    }),
  memories: (status = "current", memoryType = "") =>
    request<Memory[]>(`/memories?status=${encodeURIComponent(status)}&memory_type=${encodeURIComponent(memoryType)}`),
  createMemory: (content: string) =>
    request<{ memory: Memory; operation: string }>("/memories", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content }),
    }),
  updateMemory: (id: string, changes: Partial<Memory>) =>
    request<Memory>(`/memories/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(changes) }),
  deleteMemory: (id: string) => request<void>(`/memories/${id}`, { method: "DELETE" }),
  files: () => request<StoredFile[]>("/files"),
  upload: (file: File) => {
    const data = new FormData(); data.append("file", file);
    return request<StoredFile>("/files", { method: "POST", body: data });
  },
  settings: () => request<Record<string, unknown>>("/settings"),
  saveSettings: (values: Record<string, unknown>, apiKey?: string) =>
    request<Record<string, unknown>>("/settings", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ values, api_key: apiKey }) }),
  transcribe: (blob: Blob) => {
    const data = new FormData(); data.append("file", blob, "voice.webm");
    return request<{ transcript: string }>("/voice/transcribe", { method: "POST", body: data });
  },
  speak: async (text: string) => {
    const data = new FormData(); data.append("text", text);
    const response = await fetch(`${API_BASE}/voice/speak`, { method: "POST", body: data });
    if (!response.ok) throw new Error("Voice playback is unavailable");
    return response.blob();
  },
  exportUrl: `${API_BASE}/data/export`,
  projects: () => request<Array<{ id: string; name: string; description: string; color: string; created_at: string }>>("/projects"),
  createProject: (name: string, description: string) => request<{ id: string; name: string; description: string; color: string; created_at: string }>("/projects", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name, description }),
  }),
};
