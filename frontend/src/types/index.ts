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

