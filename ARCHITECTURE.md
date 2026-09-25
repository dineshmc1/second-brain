# Second Brain architecture

## System shape

Second Brain is a local desktop system with three process boundaries:

1. **Tauri host (Rust)** owns the Windows lifecycle, tray, global shortcuts, native windows, and packaged sidecar process.
2. **Next.js static UI (React/TypeScript)** is exported and embedded in Tauri. It has no API secret and only calls `127.0.0.1:8765`.
3. **FastAPI sidecar (Python)** owns data, retrieval, parsing, voice, credentials, and OpenRouter calls. PyInstaller turns it into a standalone executable.

```text
Tauri webview ──HTTP localhost──> FastAPI sidecar
                                      │
                     ┌────────────────┼────────────────┐
                     ▼                ▼                ▼
                  SQLite          local files     local models
               data + FTS5       uploads/audio   embedding/Whisper
                     │
                     └── selected evidence only ──> OpenRouter Chat Completions API
```

Data lives under the OS application-data directory, not the install directory. App updates do not erase knowledge.

## Important design choices

- **SQLite is the portability boundary.** Relational data, FTS indexes, graph edges, embedding metadata, and float-vector blobs stay in one database. Vector similarity is local NumPy. This avoids a fragile native vector-extension dependency in the Windows installer.
- **Local behavior does not depend on OpenRouter.** Deterministic extraction handles common facts and updates, FTS/vector search works offline, and chat returns the strongest evidence when generation is unavailable.
- **History is immutable.** An update marks the former record `superseded`, sets its effective end, and links the new record through `supersedes_memory_id`.
- **Cloud context is minimized.** OpenRouter receives the query and top-ranked excerpts—not the database or entire documents—and routes them to `openai/gpt-5.4-nano`.
- **Provider boundaries are explicit.** `LLMService`, `EmbeddingService`, and `VoiceService` can be replaced without changing repositories or HTTP contracts.
- **AI cost is bounded.** Intelligence requests use compact quick/standard/deep budgets, a local deterministic cache, a configurable daily paid-call ceiling, and useful local fallbacks. Grounded answers send at most six short evidence excerpts.
- **This is not an email agent.** The optional Google Calendar connection is a read-only private iCal feed used only for briefings. The application has no email permission and cannot modify calendar events.

## Exact folder structure

```text
Second brain/
├── frontend/                 Next.js static-export UI
│   └── src/
│       ├── app/              Home and feature routes
│       ├── components/       Shell, orb, chat, shared UI
│       ├── lib/api.ts        Typed localhost API client
│       └── types/            Frontend contracts
├── backend/
│   ├── app/
│   │   ├── api/              FastAPI route modules
│   │   ├── core/             Configuration, DB, credentials
│   │   ├── migrations/       Ordered SQLite migrations
│   │   ├── models/           Validated Pydantic contracts
│   │   ├── repositories/     Persistence access
│   │   ├── services/         Memory, RAG, LLM, voice, ingestion
│   │   └── utils/            Chunking and FTS utilities
│   ├── scripts/              Demo seeding
│   └── tests/                Unit and integration tests
├── src-tauri/                Native Windows host and bundle config
├── scripts/                  Reproducible Windows build scripts
├── assets/                   Source artwork
└── instruction.md            Exact deployment procedure
```

## Main API contracts

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/health` | Backend/database readiness and local/online mode |
| `POST` | `/api/chat` | Retrieval, optional memory action, grounded answer |
| `GET/POST` | `/api/memories` | List or create durable memories |
| `GET/PATCH/DELETE` | `/api/memories/{id}` | Inspect, version, or soft-delete memory |
| `GET/POST` | `/api/files` | List or ingest local files |
| `GET` | `/api/search?q=` | Hybrid memory/document retrieval |
| `GET/POST` | `/api/projects` | Project list and creation |
| `GET/PATCH/DELETE` | `/api/projects/{id}` | Project workspace, editing, and deletion |
| `GET/POST` | `/api/inbox` | Smart Inbox capture and triage |
| `POST` | `/api/inbox/{id}/process` | Convert a signal into memory, task, or project |
| `GET/POST/PATCH/DELETE` | `/api/tasks` | Persistent Kanban cards |
| `POST` | `/api/tasks/breakdown` | Cost-controlled complex-task decomposition |
| `GET` | `/api/intelligence/overview` | Daily briefing and weekly progress |
| `GET` | `/api/intelligence/memory-health` | Duplicate, conflict, staleness, and uncertainty scan |
| `GET` | `/api/intelligence/cognitive-twin` | Locally derived learner model |
| `GET` | `/api/intelligence/genome` | Knowledge and mastery graph data |
| `GET/POST` | `/api/learning/goals` | Goal-to-curriculum compiler and paths |
| `POST` | `/api/learning/run` | Eight adaptive learning and training modes |
| `POST` | `/api/voice/transcribe` | Local faster-whisper transcription |
| `POST` | `/api/voice/speak` | Local system TTS to WAV |
| `GET/PUT` | `/api/settings` | Settings and secure API-key update |
| `GET/POST` | `/api/data/export` | Consistent portable SQLite/metadata ZIP export |
| `POST` | `/api/data/import` | Validated restore with backup |

## Retrieval flow

1. Detect current versus historical intent.
2. Search `memories_fts` and `chunks_fts` with status/project filters.
3. Embed the query locally and cosine-score document vector blobs.
4. Merge keyword and semantic ranks using reciprocal-rank fusion.
5. Add small current-state and importance priors.
6. Send at most the top evidence items to the configured model.
7. Return answer, citations, confidence, and retrieved memory IDs.

## Intelligence layer

The intelligence layer keeps raw memory, demonstrated mastery, and execution distinct. `inbox_items` hold unprocessed signals; `tasks` power Kanban execution; `learning_goals`, `learning_nodes`, and `learning_attempts` capture capability development; and `ai_cache` plus `ai_usage` control cloud cost. The Cognitive Twin and Knowledge Genome are derived views, so they update from evidence rather than becoming unverifiable AI-written profiles.
