$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$BinaryDir = Join-Path $Root "src-tauri\binaries"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python is not installed or not on PATH. Install Python 3.12 x64."
}
if (-not (Get-Command rustc -ErrorAction SilentlyContinue)) {
    throw "Rust is not installed or not on PATH. Install the stable MSVC toolchain."
}

New-Item -ItemType Directory -Force -Path $BinaryDir | Out-Null
python -m pip install -r (Join-Path $Backend "requirements-full.txt")
python -m PyInstaller (Join-Path $Backend "second-brain-backend.spec") --noconfirm --clean --distpath (Join-Path $Backend "dist") --workpath (Join-Path $Backend "build")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed." }

$HostLine = rustc -vV | Select-String "host:"
$TargetTriple = $HostLine.Line.Split(" ")[1]
$Source = Join-Path $Backend "dist\second-brain-backend\second-brain-backend.exe"
$Target = Join-Path $BinaryDir "second-brain-backend-$TargetTriple.exe"
Copy-Item -Force -LiteralPath $Source -Destination $Target
Write-Host "Sidecar ready: $Target"
