# Build and deploy Second Brain on Windows

This is the exact clean-machine procedure. Steps 1–7 are for the developer/build PC only. The person installing `SecondBrain-Setup.exe` does **not** need Python, Node.js, Rust, npm, or a terminal.

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
3. Packages FastAPI as a target-triple-named standalone sidecar.
4. Generates all Windows icon sizes from `assets\icon.svg`.
5. Exports the Next.js UI as static assets.
6. Compiles the Rust/Tauri host.
7. Produces an NSIS installer.
8. Copies the newest installer to `release\SecondBrain-Setup.exe` and prints its SHA-256 hash.

The first build can take a long time. Do not close PowerShell while Rust or PyInstaller is working.

## 9. Locate and smoke-test the installer

The distributable file is:

```text
D:\Dinesh\Second brain\release\SecondBrain-Setup.exe
```

The installer produced and verified on 23 September 2026 is 79,733,461 bytes with SHA-256:

```text
5D41BE6DA4EF87AB5F5B764983B5A0B78732B7DB300BE2CCC3E8A6AC0F70FFB7
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

If no key is entered, the app remains useful in local/offline mode. OpenRouter usage is billed by OpenRouter under the account that created the key.

Application data is stored in:

```text
%LOCALAPPDATA%\Second Brain\
```

The log is `%LOCALAPPDATA%\Second Brain\second-brain.log`. Uploaded originals are under `%LOCALAPPDATA%\Second Brain\uploads\`.

## 11. Run the acceptance checks

Perform these checks in order:

1. Type `Remember that Project Atlas will launch in October.` Close the main window, reopen it from the tray or Start Menu, and ask `When will Project Atlas launch?` Confirm the answer says October and has a citation.
2. Type `Change Project Atlas launch to December.` Ask the current and previous launch-date questions. Confirm December is current and October is historical.
3. Upload a text PDF from **Files**, ask about a fact on a known page, and confirm the filename/page citation.
4. Ask for a personal fact that was never stored. Confirm the answer says it cannot find that information.
5. Disconnect the network. Confirm Memory, Files, Timeline, local search, capture, and evidence answers still work.
6. Reconnect, enable **Launch on Windows startup**, restart Windows, and confirm the tray app starts.
7. Press `Ctrl+Space` for quick search and `Ctrl+Alt+M` for quick capture.

## 12. Distribute it

Copy only `release\SecondBrain-Setup.exe` to the destination PC. For public distribution, code-sign both the sidecar and final installer with your organization’s Authenticode certificate before release; otherwise Windows SmartScreen may show an “unknown publisher” warning.

On the destination PC:

1. Double-click `SecondBrain-Setup.exe`.
2. Finish the current-user installation.
3. Open Second Brain from the Start Menu or desktop shortcut.
4. Enter an OpenRouter API key in Settings only if cloud-generated answers are wanted.

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
- voice model cannot initialize: verify the full build completed and allow microphone access in Windows Settings.
- scanned PDF retrieves nothing: OCR needs Tesseract; text-based PDFs work without it.
