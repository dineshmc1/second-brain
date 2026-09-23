import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.services.voice_service import get_voice_service

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/transcribe")
def transcribe(file: UploadFile = File(...)):
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    path = get_settings().data_dir / "voice" / f"{uuid4()}{suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(file.file.read())
    try:
        return {"transcript": get_voice_service().transcribe(path)}
    except Exception as exc:
        raise HTTPException(503, str(exc))


@router.post("/speak")
def speak(text: str = Form(...)):
    output = get_settings().data_dir / "voice" / f"tts-{uuid4()}.wav"
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        get_voice_service().synthesize(text, output)
        return FileResponse(output, media_type="audio/wav", filename="response.wav")
    except Exception as exc:
        raise HTTPException(503, str(exc))

