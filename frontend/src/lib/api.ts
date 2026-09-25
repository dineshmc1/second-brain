import type { ChatResponse, CognitiveTwin, Genome, InboxItem, LearningGoal, LearningMode, LearningResult, Memory, MemoryHealth, Overview, Project, ProjectDetail, SearchResult, StoredFile, Task } from "@/types";

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
  chat: (message: string, conversationId?: string, responseMode = "text", projectId?: string) =>
    request<ChatResponse>("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, conversation_id: conversationId, response_mode: responseMode, project_id: projectId }),
    }),
  memories: (status = "current", memoryType = "") =>
    request<Memory[]>(`/memories?status=${encodeURIComponent(status)}&memory_type=${encodeURIComponent(memoryType)}`),
  createMemory: (content: string, projectId?: string) =>
    request<{ memory: Memory; operation: string }>("/memories", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content, project_id: projectId }),
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
  saveSettings: (values: Record<string, unknown>, apiKey?: string, calendarUrl?: string) =>
    request<Record<string, unknown>>("/settings", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ values, api_key: apiKey, calendar_url: calendarUrl }) }),
  transcribe: (blob: Blob) => {
    const extension = blob.type.includes("ogg") ? "ogg" : blob.type.includes("mp4") ? "m4a" : "webm";
    const data = new FormData(); data.append("file", blob, `voice.${extension}`);
    return request<{ transcript: string }>("/voice/transcribe", { method: "POST", body: data });
  },
  speak: async (text: string) => {
    const data = new FormData(); data.append("text", text);
    const response = await fetch(`${API_BASE}/voice/speak`, { method: "POST", body: data });
    if (!response.ok) throw new Error("Voice playback is unavailable");
    return response.blob();
  },
  exportData: async () => {
    const response = await fetch(`${API_BASE}/data/export`, { method: "POST" });
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(body.detail ?? "Export failed");
    }
    const disposition = response.headers.get("content-disposition") ?? "";
    const filename = disposition.match(/filename="?([^";]+)"?/i)?.[1] ?? "second-brain-export.zip";
    return { blob: await response.blob(), filename };
  },
  projects: () => request<Project[]>("/projects"),
  project: (id: string) => request<ProjectDetail>(`/projects/${id}`),
  createProject: (name: string, description: string) => request<Project>("/projects", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name, description }),
  }),
  updateProject: (id: string, changes: { name?: string; description?: string; color?: string; goal?: string; status?: string }) => request<ProjectDetail>(`/projects/${id}`, {
    method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(changes),
  }),
  deleteProject: (id: string) => request<void>(`/projects/${id}`, { method: "DELETE" }),
  inbox: () => request<InboxItem[]>("/inbox"),
  captureInbox: (content: string) => request<InboxItem>("/inbox", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content }),
  }),
  processInbox: (id: string, action: "memory" | "task" | "project" | "archive" | "discard", projectId?: string) =>
    request<{ processed: boolean }>(`/inbox/${id}/process`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action, project_id: projectId }),
    }),
  tasks: (projectId?: string) => request<Task[]>(`/tasks${projectId ? `?project_id=${encodeURIComponent(projectId)}` : ""}`),
  createTask: (task: Partial<Task> & { title: string }) => request<Task>("/tasks", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(task),
  }),
  updateTask: (id: string, changes: Partial<Task>) => request<Task>(`/tasks/${id}`, {
    method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(changes),
  }),
  deleteTask: (id: string) => request<void>(`/tasks/${id}`, { method: "DELETE" }),
  breakdownTask: (title: string, projectId?: string) => request<{ parent: Task; cards: Task[]; ai_used: boolean }>("/tasks/breakdown", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title, project_id: projectId }),
  }),
  organizeTasks: (projectId?: string) => request<{ organized: number; strategy: string }>(`/tasks/organize${projectId ? `?project_id=${encodeURIComponent(projectId)}` : ""}`, { method: "POST" }),
  overview: () => request<Overview>("/intelligence/overview"),
  memoryHealth: () => request<MemoryHealth>("/intelligence/memory-health"),
  cognitiveTwin: () => request<CognitiveTwin>("/intelligence/cognitive-twin"),
  genome: () => request<Genome>("/intelligence/genome"),
  search: (query: string, projectId?: string) => request<SearchResult[]>(`/search?q=${encodeURIComponent(query)}${projectId ? `&project_id=${encodeURIComponent(projectId)}` : ""}`),
  learningGoals: () => request<LearningGoal[]>("/learning/goals"),
  createLearningGoal: (title: string, objective: string) => request<LearningGoal>("/learning/goals", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title, objective }),
  }),
  updateLearningNode: (id: string, changes: { status?: string; mastery?: number }) => request(`/learning/nodes/${id}`, {
    method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(changes),
  }),
  runLearning: (mode: LearningMode, input: string, depth = "standard", goalId?: string, nodeId?: string) => request<LearningResult>("/learning/run", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ mode, input, depth, goal_id: goalId, node_id: nodeId }),
  }),
  aiUsage: () => request<{ calls: number; input_tokens: number; output_tokens: number; cache_hits: number }>("/learning/usage"),
};
