from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

root = Path(SPECPATH)
voice_model = root / "models" / "faster-whisper-tiny.en"
datas = [(str(root / "app" / "migrations"), "app/migrations")]
datas += collect_data_files("faster_whisper")
if voice_model.exists():
    datas.append((str(voice_model), "models/faster-whisper-tiny.en"))
hiddenimports = [
    "uvicorn.logging", "uvicorn.loops.auto", "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto", "keyring.backends.Windows",
    "fastembed", "faster_whisper", "pyttsx3.drivers", "pyttsx3.drivers.sapi5",
]

a = Analysis(
    [str(root / "app" / "main.py")],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    name="second-brain-backend", debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, console=False, disable_windowed_traceback=False,
    exclude_binaries=True,
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False, upx=True, upx_exclude=[], name="second-brain-backend",
)
