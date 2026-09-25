# Second Brain

A local-first Windows cognitive operating system for memory, project execution, source-grounded reasoning, and accelerated learning.

## Implemented system

- JARVIS-inspired Command Center, Smart Inbox, Kanban, Project Cockpit, Learning Lab, Intelligence Dashboard, search, chat, memory, and sources
- FastAPI sidecar packaged with PyInstaller and launched automatically by Tauri
- SQLite migrations, FTS5, local embeddings, hybrid ranking, and source citations
- Persistent creation, direct editing with version history, duplicate confirmation, updates, and superseded history
- PDF, DOCX, TXT, Markdown, and image ingestion with page/chunk preservation
- GPT-5.4 Nano through OpenRouter's OpenAI-compatible Chat Completions API behind `LLMService`
- Bundled offline faster-whisper transcription, Windows voice playback, and visible microphone status/errors
- Windows Credential Manager API-key storage
- NSIS installer without console windows, tray, startup option, and dismissible quick search/capture
- In-place ZIP export/import, actionable project workspaces, and offline evidence answers
- Read-only Google Calendar briefings through a private iCal feed stored in Windows Credential Manager
- Daily briefings, numerical weekly reviews, project progress, and smart project-memory resurfacing
- Local duplicate, conflict, staleness, and uncertainty detection for memory health
- Cognitive Twin and Knowledge Genome derived from real memories and demonstrated learning
- Goal-to-curriculum compiler plus eight accelerated learning and training modes
- Low-cost AI controls: compact context, local caching/fallbacks, usage meter, and a daily paid-call ceiling

## Development

Install Python 3.12 x64, the current Node.js LTS, Rust MSVC stable, and Visual Studio Build Tools with “Desktop development with C++”. Then:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements-dev.txt
npm install
npm --prefix frontend install
npm run dev
```

The browser UI is at `http://localhost:3000`; the local API is at `http://127.0.0.1:8765`. `npm run dev` starts the API and Tauri.

## Test

```powershell
.\.venv\Scripts\Activate.ps1
npm test
```

## Production

Follow [`instruction.md`](instruction.md). The installer is emitted beneath:

```text
src-tauri\target\release\bundle\nsis\Second Brain_0.2.0_x64-setup.exe
```

Installed users do not need Python, Node.js, Rust, npm, or a terminal. This is a Tauri desktop app, so use the included GitHub Actions workflow or a local Windows build—not Vercel—to produce the installer.

## Privacy

Documents, audio, database records, calendar credentials, learning history, indexes, and embeddings stay local. Only an explicit learning request or a question with a small set of selected evidence is sent through OpenRouter. Without a key or internet, local capture, planning, health analysis, curriculum fallback, search, retrieval, and evidence answers remain available.

## Troubleshooting

- **Backend offline:** verify port 8765 is free and inspect `%LOCALAPPDATA%\Second Brain\Second Brain\second-brain.log`.
- **Scanned PDF has no text:** install Tesseract OCR or upload screenshots. PDF OCR is optional.
- **First embedding is slow:** the full build initializes local BGE on first indexing; if unavailable, deterministic local embeddings are used.
- **Microphone fails:** allow microphone access in Windows Privacy settings and use the full sidecar build.
- **Shortcut does not open:** another program may own it. Exit that program or use the main window.
- **Build cannot find `link.exe`:** install Visual Studio 2022 C++ Desktop workload and reopen PowerShell.
- **WebView fails:** install or repair Microsoft Edge WebView2 Runtime.
