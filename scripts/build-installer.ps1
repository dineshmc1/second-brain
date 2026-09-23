$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ReleaseDir = Join-Path $Root "release"

Push-Location $Root
try {
    npm run test
    if ($LASTEXITCODE -ne 0) { throw "Tests failed. Installer was not built." }
    npm run build:desktop
    if ($LASTEXITCODE -ne 0) { throw "Desktop build failed." }

    $BundleDir = Join-Path $Root "src-tauri\target\release\bundle\nsis"
    $Installer = Get-ChildItem -LiteralPath $BundleDir -Filter "*.exe" |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if (-not $Installer) { throw "NSIS installer was not found under $BundleDir" }

    New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
    $Final = Join-Path $ReleaseDir "SecondBrain-Setup.exe"
    Copy-Item -Force -LiteralPath $Installer.FullName -Destination $Final
    $Hash = Get-FileHash -Algorithm SHA256 -LiteralPath $Final
    Write-Host "Installer: $Final"
    Write-Host "SHA256: $($Hash.Hash)"
} finally {
    Pop-Location
}

