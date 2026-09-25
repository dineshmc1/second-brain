from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings


class VoiceService:
    def __init__(self) -> None:
        self._whisper = None

    def transcribe(self, audio_path: Path) -> str:
        try:
            if self._whisper is None:
                from faster_whisper import WhisperModel

                settings = get_settings()
                bundled = settings.resource_dir / "models" / "faster-whisper-tiny.en"
                model = str(bundled) if bundled.exists() else "tiny.en"
                download_root = settings.data_dir / "models" / "whisper"
                download_root.mkdir(parents=True, exist_ok=True)
                self._whisper = WhisperModel(
                    model,
                    device="cpu",
                    compute_type="int8",
                    download_root=str(download_root),
                )
            segments, _ = self._whisper.transcribe(str(audio_path), vad_filter=True)
            transcript = " ".join(segment.text.strip() for segment in segments).strip()
            if not transcript:
                raise RuntimeError("No speech was detected. Try speaking closer to the microphone.")
            return transcript
        except ImportError as exc:
            raise RuntimeError("Local speech recognition is not installed in this build") from exc

    def synthesize(self, text: str, output: Path) -> Path:
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.save_to_file(text, str(output))
            engine.runAndWait()
            engine.stop()
            if not output.exists() or output.stat().st_size == 0:
                raise RuntimeError("Windows text-to-speech did not produce audio")
            return output
        except ImportError as exc:
            raise RuntimeError("Local text-to-speech is not installed in this build") from exc


@lru_cache
def get_voice_service() -> VoiceService:
    return VoiceService()
