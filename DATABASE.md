# Database schema

The first migration is [`backend/app/migrations/001_initial.sql`](backend/app/migrations/001_initial.sql). Migrations are applied once and recorded in `schema_migrations`.

| Table | Responsibility | Important indexes/relations |
|---|---|---|
| `settings` | Non-secret JSON settings | Primary key `key` |
| `projects` | Project scopes | Unique project name |
| `memories` | Current and historical facts | `(entity, property_key, status)`, project/status, `supersedes_memory_id` |
| `memories_fts` | Memory keyword search | FTS5 virtual table |
| `memory_versions` | Snapshots before manual edits | FK to memory |
| `files` | Original local file metadata | Local path is never returned by API |
| `document_chunks` | Page-aware text and vector blobs | Unique `(file_id, chunk_number)` |
| `chunks_fts` | Document keyword search | FTS5 virtual table |
| `embedding_metadata` | Embedding model and dimensions | Owner compound key |
| `conversations` / `messages` | Persistent chat history | Conversation/time index |
| `tasks` | Actionable memories | Optional project/memory FKs |
| `entities` / `relationships` | Lightweight graph | Unique typed edges |
| `voice_notes` | Recording/transcript metadata | Local path only |

Memory statuses are `current`, `superseded`, `historical`, `uncertain`, and soft-`deleted`. Current retrieval excludes superseded knowledge unless the question asks for history.

The OpenRouter API key is deliberately absent from SQLite. Python `keyring` stores it in Windows Credential Manager.
