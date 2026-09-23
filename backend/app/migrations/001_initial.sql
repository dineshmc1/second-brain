CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    color TEXT NOT NULL DEFAULT '#68e8ff',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    memory_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    normalized_fact TEXT NOT NULL,
    entity TEXT,
    property_key TEXT,
    category TEXT,
    tags_json TEXT NOT NULL DEFAULT '[]',
    source_type TEXT NOT NULL DEFAULT 'conversation',
    source_id TEXT,
    project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    effective_from TEXT,
    effective_until TEXT,
    importance_score REAL NOT NULL DEFAULT 0.5 CHECK (importance_score BETWEEN 0 AND 1),
    confidence_score REAL NOT NULL DEFAULT 0.8 CHECK (confidence_score BETWEEN 0 AND 1),
    status TEXT NOT NULL DEFAULT 'current' CHECK (status IN ('current','historical','superseded','deleted','uncertain')),
    supersedes_memory_id TEXT REFERENCES memories(id) ON DELETE SET NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_memories_entity_property ON memories(entity, property_key, status);
CREATE INDEX IF NOT EXISTS idx_memories_status_created ON memories(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project_id, status);

CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    memory_id UNINDEXED, title, content, normalized_fact, entity, tags
);

CREATE TABLE IF NOT EXISTS memory_versions (
    id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    snapshot_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    title TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    page_count INTEGER,
    tags_json TEXT NOT NULL DEFAULT '[]',
    topics_json TEXT NOT NULL DEFAULT '[]',
    imported_at TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'upload',
    status TEXT NOT NULL DEFAULT 'ready',
    error TEXT
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    page INTEGER,
    chunk_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    embedding BLOB,
    embedding_dim INTEGER,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE(file_id, chunk_number)
);
CREATE INDEX IF NOT EXISTS idx_chunks_file_page ON document_chunks(file_id, page, chunk_number);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(chunk_id UNINDEXED, text);

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT 'New conversation',
    project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user','assistant','system')),
    content TEXT NOT NULL,
    citations_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open',
    due_at TEXT,
    project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
    source_memory_id TEXT REFERENCES memories(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    entity_type TEXT NOT NULL DEFAULT 'concept',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, entity_type)
);

CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    score REAL NOT NULL DEFAULT 0.5,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, target_id, relationship_type)
);

CREATE TABLE IF NOT EXISTS embedding_metadata (
    owner_type TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    model TEXT NOT NULL,
    dimensions INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(owner_type, owner_id)
);

CREATE TABLE IF NOT EXISTS voice_notes (
    id TEXT PRIMARY KEY,
    filepath TEXT NOT NULL,
    transcript TEXT,
    duration_seconds REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

