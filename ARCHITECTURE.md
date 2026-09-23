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
| `GET/POST` | `/api/projects` | Project scopes |
| `POST` | `/api/voice/transcribe` | Local faster-whisper transcription |
| `POST` | `/api/voice/speak` | Local system TTS to WAV |
| `GET/PUT` | `/api/settings` | Settings and secure API-key update |
| `POST` | `/api/data/export` | Portable ZIP export |
| `POST` | `/api/data/import` | Validated restore with backup |

## Retrieval flow

1. Detect current versus historical intent.
2. Search `memories_fts` and `chunks_fts` with status/project filters.
3. Embed the query locally and cosine-score document vector blobs.
4. Merge keyword and semantic ranks using reciprocal-rank fusion.
5. Add small current-state and importance priors.
6. Send at most the top evidence items to the configured model.
7. Return answer, citations, confidence, and retrieved memory IDs.

## Deferred post-MVP modules

The schema supports entities/relationships and the UI contains the graph entry point. Automated graph extraction, rich graph editing, streaming tokens, configurable shortcut recording, and a full Brain Dump review queue remain post-MVP work; none blocks the persistence/RAG acceptance path.
