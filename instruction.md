# Build and deploy Second Brain on Windows

This is the exact clean-machine procedure. Steps 1–7 are for the developer/build PC only. The person installing `SecondBrain-Setup.exe` does **not** need Python, Node.js, Rust, npm, or a terminal.

## Choose the correct deployment target

This repository is a Windows desktop application, not a Vercel web application. Do **not** connect the whole repository to Vercel. The browser UI depends on a local Tauri host, a packaged Python sidecar on `127.0.0.1`, Windows Credential Manager, and a local SQLite database. A standalone Vercel deployment would only publish an incomplete UI.

Use one of these supported distribution paths:

- Build `SecondBrain-Setup.exe` locally by following steps 1–9 below.
- Push the code to GitHub and use the included GitHub Actions workflow, as described under **Build and download through GitHub**.

No build-time API key or cloud database is required. Each installed user enters their own OpenRouter key inside the desktop app.

## 1. Use a supported Windows build machine

Use 64-bit Windows 10 (version 1803 or later) or Windows 11. Sign in as a user who may install developer tools. Keep at least 15 GB free because Python voice/embedding packages and the Rust build cache are large.

Open **PowerShell as Administrator** and run:

```powershell
winget --version
```

If Windows says `winget` is missing, install or update **App Installer** from Microsoft Store, then reopen PowerShell.

## 2. Install the build toolchain

Run these commands one at a time:

```powershell
winget install --exact --id Python.Python.3.12
winget install --exact --id OpenJS.NodeJS.LTS
winget install --exact --id Rustlang.Rustup
winget install --exact --id Microsoft.VisualStudio.2022.BuildTools --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

Restart Windows after Visual Studio Build Tools finishes. This makes every PATH and compiler change deterministic.

## 3. Verify prerequisites

Open a new normal PowerShell window and run:

```powershell
py -3.12 --version
node --version
npm --version
rustc --version
cargo --version
```

All five commands must print a version. If `rustc` is missing, run `$env:USERPROFILE\.cargo\bin\rustup.exe default stable-msvc`, close PowerShell, and check again.

## 4. Open the source folder

```powershell
Set-Location "D:\Dinesh\Second brain"
```

If you copied this project elsewhere, replace that path with the folder containing this `instruction.md` and `package.json`.

## 5. Create the isolated Python build environment

```powershell
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip wheel
python -m pip install -r backend\requirements-dev.txt
```

Leave this window open and the virtual environment active for the remaining build steps.

## 6. Install JavaScript dependencies

```powershell
npm install
npm --prefix frontend install
```

Do not use `--force` or `--legacy-peer-deps`. A dependency error should be fixed rather than hidden.

## 7. Verify the source before packaging

```powershell
npm test
```

Expected result:

- Python tests finish with no failures.
- TypeScript finishes with no errors.

Optional development run:

```powershell
npm run dev
```

The FastAPI service starts on `127.0.0.1:8765` and Tauri opens the desktop UI. Press `Ctrl+C` once to stop both processes before packaging.

## 8. Build the production installer

With `.venv` still active, run:

```powershell
npm run build
```

The build script performs these actions in order:

1. Runs backend tests and frontend type checking.
2. Installs full local embedding, Whisper, TTS, and PyInstaller dependencies.
3. Downloads and bundles the `faster-whisper-tiny.en` model for offline speech recognition.
4. Packages FastAPI as a windowless, target-triple-named standalone sidecar.
5. Generates all Windows icon sizes from `assets\icon.svg`.
6. Exports the Next.js UI as static assets.
7. Compiles the windowless Rust/Tauri host.
8. Produces an NSIS installer.
9. Copies the newest installer to `release\SecondBrain-Setup.exe` and prints its SHA-256 hash.

The first build can take a long time. Do not close PowerShell while Rust or PyInstaller is working.

## 9. Locate and smoke-test the installer

The distributable file is:

```text
D:\Dinesh\Second brain\release\SecondBrain-Setup.exe
```

The version 0.2.0 installer produced and verified on 24 September 2026 is 149,460,787 bytes with SHA-256:

```text
9344B77272471AC004BA02A228F94C4AD096A421F6766E18DA8DA8762FFF1C3B
```

Rebuilding later will produce a different hash. Always use the hash printed by `npm run build` for that build.

Run it on the build PC:

```powershell
.\release\SecondBrain-Setup.exe
```

Finish the installer, then launch **Second Brain** from the Start Menu or desktop shortcut. You must not start Python, npm, or FastAPI separately.

## 10. Configure the installed app

1. Go to `https://openrouter.ai/` in a browser and sign in or create an account.
2. Add OpenRouter credits if the account has no usable balance.
3. Open `https://openrouter.ai/settings/keys` and click **Create API Key**.
4. Give the key a name such as `Second Brain`, create it, and copy it immediately.
5. Open **Second Brain → Settings → AI**.
6. Paste the key into **OpenRouter API key**.
7. Confirm **OpenRouter model** is `openai/gpt-5.4-nano`.
8. Click **Save changes**. The key is stored in Windows Credential Manager, not SQLite.
9. Open **Chat** and ask a question. The status should report online mode when the key and network are available.

For the lowest API cost, keep **AI cost control → Cache identical AI work** enabled, select **Quick · lowest tokens**, and choose a daily paid-call ceiling. Search, memory health, Cognitive Twin, Knowledge Genome, project resurfacing, Kanban organization, and fallback curricula run locally. OpenRouter is used only for explicit generation and source-backed synthesis.

To add read-only Google Calendar context:

1. In Google Calendar on the web, open **Settings → Settings for my calendars → your calendar → Integrate calendar**.
2. Copy the **Secret address in iCal format**. Treat this URL as a password.
3. In Second Brain, open **Settings → Google Calendar · read only** and paste the URL.
4. Save, then return to **Command**. Upcoming events appear in the daily briefing.

This connection is deliberately one-way. Second Brain cannot create or edit events and has no email permissions. The secret address is stored in Windows Credential Manager.

To use voice input, click the microphone once, speak, then click the square Stop button. Wait for **Transcribing locally…** to finish; the recognized words appear in the message box for review before sending. To hear responses automatically, choose **Voice only** or **Text + voice** and save Settings. Every assistant message also has a **Read aloud** button.

If no key is entered, the app remains useful in local/offline mode. OpenRouter usage is billed by OpenRouter under the account that created the key.

Application data is stored in:

```text
%LOCALAPPDATA%\Second Brain\Second Brain\
```

The SQLite database is `%LOCALAPPDATA%\Second Brain\Second Brain\second_brain.sqlite3`. The log is in the same directory as `second-brain.log`, and uploaded originals are under its `uploads\` folder.

You do not need Supabase, PostgreSQL, Neon, Vercel Storage, or any other hosted database. Every Windows user gets a private local database. Use **Settings → Export Second Brain** to make a portable backup before moving computers or uninstalling.

## 11. Run the acceptance checks

Perform these checks in order:

1. Type `Remember that Project Atlas will launch in October.` Close the main window, reopen it from the tray or Start Menu, and ask `When will Project Atlas launch?` Confirm the answer says October and has a citation.
2. Open **Memory**, select that memory, change its title and fact, and save. Confirm the card and search results show the edited values.
3. Type `Change Project Atlas launch to December.` Ask the current and previous launch-date questions. Confirm December is current and October is historical.
4. Press `Ctrl+Space` for quick search. Close it with the X button, Escape, or `Ctrl+Space` again. Repeat for quick capture with `Ctrl+Alt+M`.
5. Confirm no terminal or command window appears when Second Brain starts.
6. Select **Settings → Export Second Brain**. Confirm a ZIP downloads, the Settings page remains open, and the **Back** button works.
7. Set response mode to **Voice only**, save, ask a question, and confirm Windows reads the answer aloud. Use **Read aloud** to replay it.
8. Click the microphone, speak, click Stop, and confirm the transcript appears in the message box.
9. Create a project, open its card, add a project memory, ask a project question, edit the project details, and confirm its memory/chat counters update.
10. Upload a text PDF from **Files**, ask about a fact on a known page, and confirm the filename/page citation.
11. Ask for a personal fact that was never stored. Confirm the answer says it cannot find that information.
12. Disconnect the network. Confirm Memory, Files, Timeline, project memories, local search, capture, transcription, and evidence answers still work.
13. Reconnect, enable **Launch on Windows startup**, restart Windows, and confirm the tray app starts.
14. Capture three rough thoughts through Quick Capture. Open **Smart Inbox** and route them into a memory, task, and project.
15. Add a complex outcome in **Kanban**, enable **Break down with AI**, generate cards, drag cards between columns, and run **AI organize**.
16. Confirm **Command** shows the daily briefing, Google Calendar events, and a numerical weekly progress bar.
17. Open a Project Cockpit and confirm progress, execution snapshot, source-backed questions, and Smart Resurfacing work.
18. Open **Intelligence** and confirm Memory Health, Cognitive Twin, and Knowledge Genome load without an API call.
19. Compile a goal in **Learning Lab**, complete one node, and run all eight training modes. Repeat an identical request and confirm it reports **Cached**.

## 12. Distribute it

Copy only `release\SecondBrain-Setup.exe` to the destination PC. For public distribution, code-sign both the sidecar and final installer with your organization’s Authenticode certificate before release; otherwise Windows SmartScreen may show an “unknown publisher” warning.

On the destination PC:

1. Double-click `SecondBrain-Setup.exe`.
2. Finish the current-user installation.
3. Open Second Brain from the Start Menu or desktop shortcut.
4. Enter an OpenRouter API key in Settings only if cloud-generated answers are wanted.

## Build and download through GitHub

The repository includes `.github/workflows/windows-installer.yml`. It builds on a GitHub-hosted Windows runner, so your own PC does not need the build toolchain.

### Upload the source

Create an empty GitHub repository. In PowerShell at this project's root, run:

```powershell
git add .
git commit -m "Build Second Brain desktop app"
git branch -M main
git remote add origin https://github.com/YOUR-NAME/YOUR-REPOSITORY.git
git push -u origin main
```

Do not commit `.env`, an OpenRouter key, the local database, or user uploads. The included `.gitignore` already excludes them. Before pushing, confirm `git status` does not list `.env`.

### Make a test installer without publishing a release

1. Open the GitHub repository.
2. Select **Actions → Build Windows installer**.
3. Click **Run workflow**, choose `main`, and confirm.
4. Wait for the green check mark. The full build can take 15–40 minutes.
5. Open the completed workflow run.
6. Under **Artifacts**, download `SecondBrain-Windows-Installer`.
7. Unzip it and run the `.exe` inside.

GitHub workflow artifacts are ZIP downloads and are intended for testing. For a permanent public download, publish a release.

### Publish a permanent GitHub Release

For the first release, run:

```powershell
git tag v0.2.0
git push origin v0.2.0
```

The tag triggers the same workflow and creates a GitHub Release with the Windows installer attached. Users then open the repository's **Releases** page, choose the latest release, and download the `.exe` from **Assets**.

Before a later release, update the version in `package.json`, `frontend\package.json`, `src-tauri\tauri.conf.json`, and `src-tauri\Cargo.toml`, commit the changes, then create and push a new matching tag such as `v0.1.2`.

### Environment variables and secrets

For the desktop build, add **no environment variables** to Vercel or GitHub. In particular, never create `NEXT_PUBLIC_OPENROUTER_API_KEY`: any `NEXT_PUBLIC_` value is embedded in browser JavaScript and can be read by other people.

For local developer-only testing, you may copy `.env.example` to `.env` and set:

```dotenv
OPENROUTER_API_KEY=sk-or-v1-your-key-here
SECOND_BRAIN_MODEL=openai/gpt-5.4-nano
```

Do not commit `.env`. The distributed installer does not contain this key; users add it in **Settings → AI**, where it is saved by Windows Credential Manager.

## Clean rebuild

Normal builds are incremental. If a release build becomes corrupted, close the app and remove only generated build folders:

```powershell
Remove-Item -Recurse -Force -LiteralPath frontend\.next -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force -LiteralPath frontend\out -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force -LiteralPath backend\build -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force -LiteralPath backend\dist -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force -LiteralPath src-tauri\target -ErrorAction SilentlyContinue
npm run build
```

These commands remove generated artifacts only. They do not touch installed user data under `%LOCALAPPDATA%\Second Brain`.

## Common failures

- `python` not found: activate `.venv`, then use `python`; create it again with `py -3.12 -m venv .venv` if needed.
- `link.exe` not found: repair Visual Studio Build Tools and select **Desktop development with C++** plus the Windows SDK.
- `failed to bundle sidecar`: run `npm run build:backend` and verify `src-tauri\binaries\second-brain-backend-x86_64-pc-windows-msvc.exe` exists.
- port 8765 already in use: stop the other process with `Get-NetTCPConnection -LocalPort 8765`, then relaunch.
- blank app window: install Microsoft Edge WebView2 Runtime and inspect the local log.
- microphone permission denied: enable desktop-app microphone access in **Windows Settings → Privacy & security → Microphone**, then restart Second Brain.
- voice transcription fails: verify the full build completed and that the installer is approximately 149 MB; smaller older installers do not contain the bundled model.
- scanned PDF retrieves nothing: OCR needs Tesseract; text-based PDFs work without it.
