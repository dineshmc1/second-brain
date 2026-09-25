export type Citation = {
  id: string;
  source_type: string;
  label: string;
  page?: number | null;
  excerpt: string;
  score: number;
};

export type ChatResponse = {
  answer: string;
  citations: Citation[];
  confidence: number;
  retrieved_memory_ids: string[];
  conversation_id: string;
  memory_action?: string | null;
  offline: boolean;
};

export type Memory = {
  id: string;
  memory_type: string;
  title: string;
  content: string;
  normalized_fact: string;
  entity?: string | null;
  property_key?: string | null;
  category?: string | null;
  tags: string[];
  source_type: string;
  project_id?: string | null;
  created_at: string;
  updated_at: string;
  importance_score: number;
  confidence_score: number;
  status: string;
  supersedes_memory_id?: string | null;
};

export type StoredFile = {
  id: string;
  filename: string;
  title: string;
  mime_type: string;
  size_bytes: number;
  page_count?: number | null;
  chunk_count: number;
  imported_at: string;
  status: string;
  error?: string | null;
};

export type Project = {
  id: string;
  name: string;
  description: string;
  color: string;
  created_at: string;
  updated_at: string;
  memory_count: number;
  conversation_count: number;
  task_count: number;
  total_task_count: number;
  completed_task_count: number;
  progress: number;
  goal: string;
  status: "active" | "paused" | "completed" | "archived";
};

export type ProjectDetail = Project & {
  memories: Array<Pick<Memory, "id" | "title" | "normalized_fact" | "memory_type" | "importance_score" | "updated_at">>;
  conversations: Array<{ id: string; title: string; created_at: string; updated_at: string }>;
  tasks: Task[];
  resurfaced: ResurfacedMemory[];
};

export type InboxItem = {
  id: string;
  content: string;
  source_type: string;
  status: string;
  suggested_type: "memory" | "task" | "project";
  suggested_project_id?: string | null;
  created_at: string;
};

export type Task = {
  id: string;
  title: string;
  description: string;
  status: "backlog" | "next" | "in_progress" | "blocked" | "done";
  priority: "low" | "medium" | "high" | "critical";
  due_at?: string | null;
  project_id?: string | null;
  project_name?: string | null;
  project_color?: string | null;
  parent_task_id?: string | null;
  position: number;
  updated_at: string;
};

export type CalendarEvent = {
  id: string;
  title: string;
  start: string;
  all_day: boolean;
  location: string;
  description: string;
};

export type Overview = {
  generated_at: string;
  inbox_count: number;
  today_tasks: Task[];
  calendar_events: CalendarEvent[];
  calendar_error?: string | null;
  weekly: { completed: number; created: number; remaining: number; progress: number };
  metrics: { current_memories: number; active_projects: number; mastered_nodes: number; total_nodes: number };
};

export type MemoryHealthIssue = {
  kind: "duplicate" | "outdated" | "conflict" | "uncertain";
  reason: string;
  memory: { id: string; title: string; fact: string };
  related?: { id: string; title: string; fact: string } | null;
  similarity?: number | null;
};

export type MemoryHealth = {
  score: number;
  counts: Record<string, number>;
  issues: MemoryHealthIssue[];
  scanned: number;
};

export type CognitiveTwin = {
  knowledge_count: number;
  confidence: number;
  dominant_memory_types: Array<[string, number]>;
  strongest_domains: Array<[string, number]>;
  learning_modes_used: Array<[string, number]>;
  recurring_misconceptions: Array<[string, number]>;
  preferences: { explanation_style: string; challenge_level: string; session_minutes: number };
  insight: string;
};

export type Genome = {
  concepts: Array<{ name: string; evidence: number; confidence: number }>;
  goals: LearningGoal[];
  nodes: LearningNode[];
};

export type LearningNode = {
  id: string;
  goal_id: string;
  title: string;
  description: string;
  node_type: string;
  status: "locked" | "ready" | "learning" | "mastered";
  mastery: number;
  sequence: number;
};

export type LearningGoal = {
  id: string;
  title: string;
  objective: string;
  status: string;
  progress: number;
  target_date?: string | null;
  nodes: LearningNode[];
  generated_with_ai?: boolean;
};

export type LearningMode = "accelerate" | "explain" | "misconception" | "compress" | "transfer" | "simulate" | "experts" | "communication";

export type LearningResult = {
  result: string;
  local: boolean;
  cache_hit: boolean;
  input_tokens: number;
  output_tokens: number;
  misconceptions: string[];
  score?: number | null;
};

export type ResurfacedMemory = {
  id: string;
  title: string;
  normalized_fact: string;
  memory_type: string;
  reason: string;
  resurface_score: number;
};

export type SearchResult = {
  id: string;
  kind: string;
  title: string;
  excerpt: string;
  score: number;
  source_type: string;
  page?: number | null;
};
