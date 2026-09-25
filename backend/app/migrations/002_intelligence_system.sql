ALTER TABLE projects ADD COLUMN goal TEXT NOT NULL DEFAULT '';
ALTER TABLE projects ADD COLUMN status TEXT NOT NULL DEFAULT 'active';

ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium';
ALTER TABLE tasks ADD COLUMN position INTEGER NOT NULL DEFAULT 0;
ALTER TABLE tasks ADD COLUMN completed_at TEXT;
ALTER TABLE tasks ADD COLUMN parent_task_id TEXT REFERENCES tasks(id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS inbox_items (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'capture',
    status TEXT NOT NULL DEFAULT 'unprocessed',
    suggested_type TEXT,
    suggested_project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    processed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_inbox_status_created ON inbox_items(status, created_at DESC);

CREATE TABLE IF NOT EXISTS learning_goals (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    objective TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    progress REAL NOT NULL DEFAULT 0,
    target_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS learning_nodes (
    id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES learning_goals(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    node_type TEXT NOT NULL DEFAULT 'concept',
    status TEXT NOT NULL DEFAULT 'locked',
    mastery REAL NOT NULL DEFAULT 0,
    sequence INTEGER NOT NULL DEFAULT 0,
    prerequisites_json TEXT NOT NULL DEFAULT '[]',
    evidence_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_learning_nodes_goal ON learning_nodes(goal_id, sequence);

CREATE TABLE IF NOT EXISTS learning_attempts (
    id TEXT PRIMARY KEY,
    goal_id TEXT REFERENCES learning_goals(id) ON DELETE CASCADE,
    node_id TEXT REFERENCES learning_nodes(id) ON DELETE SET NULL,
    mode TEXT NOT NULL,
    prompt TEXT NOT NULL,
    result TEXT NOT NULL,
    score REAL,
    misconceptions_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_cache (
    cache_key TEXT PRIMARY KEY,
    mode TEXT NOT NULL,
    response_text TEXT NOT NULL,
    input_chars INTEGER NOT NULL DEFAULT 0,
    output_chars INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_usage (
    id TEXT PRIMARY KEY,
    mode TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cache_hit INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ai_usage_created ON ai_usage(created_at DESC);
