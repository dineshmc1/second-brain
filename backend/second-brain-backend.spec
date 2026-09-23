from pathlib import Path

root = Path(SPECPATH)
hiddenimports = [
    "uvicorn.logging", "uvicorn.loops.auto", "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto", "keyring.backends.Windows",
    "fastembed", "faster_whisper", "pyttsx3.drivers", "pyttsx3.drivers.sapi5",
]

a = Analysis(
    [str(root / "app" / "main.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[(str(root / "app" / "migrations"), "app/migrations")],
    hiddenimports=hiddenimports,
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    name="second-brain-backend", debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, console=True, hide_console="hide-early", disable_windowed_traceback=False,
    exclude_binaries=True,
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False, upx=True, upx_exclude=[], name="second-brain-backend",
)
