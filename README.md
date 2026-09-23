# Second Brain

A local-first Windows AI knowledge assistant with temporal memory, document RAG, citations, offline search, voice capture, and a Tauri desktop shell.

## Implemented MVP

- JARVIS-inspired Next.js interface with Home, Chat, Memory, Files, Timeline, Projects, Graph, and Settings
- FastAPI sidecar packaged with PyInstaller and launched automatically by Tauri
- SQLite migrations, FTS5, local embeddings, hybrid ranking, and source citations
- Persistent creation, duplicate confirmation, updates, and superseded history
- PDF, DOCX, TXT, Markdown, and image ingestion with page/chunk preservation
- GPT-5.4 Nano through OpenRouter's OpenAI-compatible Chat Completions API behind `LLMService`
- Local faster-whisper and Windows TTS abstractions
- Windows Credential Manager API-key storage
- NSIS installer, tray, startup option, quick search, and quick capture
- ZIP export/import and offline evidence answers

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
src-tauri\target\release\bundle\nsis\Second Brain_0.1.0_x64-setup.exe
```

Installed users do not need Python, Node.js, Rust, npm, or a terminal.

## Privacy

Documents, audio, database records, keyword indexes, and embeddings stay local. Only the question and selected evidence are sent through OpenRouter to GPT-5.4 Nano when a key is configured. Without a key or internet, local creation, browsing, search, retrieval, and evidence answers remain available.

## Troubleshooting

- **Backend offline:** verify port 8765 is free and inspect `%LOCALAPPDATA%\Second Brain\second-brain.log`.
- **Scanned PDF has no text:** install Tesseract OCR or upload screenshots. PDF OCR is optional.
- **First embedding is slow:** the full build initializes local BGE on first indexing; if unavailable, deterministic local embeddings are used.
- **Microphone fails:** allow microphone access in Windows Privacy settings and use the full sidecar build.
- **Shortcut does not open:** another program may own it. Exit that program or use the main window.
- **Build cannot find `link.exe`:** install Visual Studio 2022 C++ Desktop workload and reopen PowerShell.
- **WebView fails:** install or repair Microsoft Edge WebView2 Runtime.
