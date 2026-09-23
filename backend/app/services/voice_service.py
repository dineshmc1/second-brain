from __future__ import annotations

import tempfile
from functools import lru_cache
from pathlib import Path


class VoiceService:
    def __init__(self) -> None:
        self._whisper = None

    def transcribe(self, audio_path: Path) -> str:
        try:
            if self._whisper is None:
                from faster_whisper import WhisperModel

                self._whisper = WhisperModel("base.en", device="cpu", compute_type="int8")
            segments, _ = self._whisper.transcribe(str(audio_path), vad_filter=True)
            return " ".join(segment.text.strip() for segment in segments).strip()
        except ImportError as exc:
            raise RuntimeError("Local speech recognition is not installed in this build") from exc

    def synthesize(self, text: str, output: Path) -> Path:
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.save_to_file(text, str(output))
            engine.runAndWait()
            return output
        except ImportError as exc:
            raise RuntimeError("Local text-to-speech is not installed in this build") from exc


@lru_cache
def get_voice_service() -> VoiceService:
    return VoiceService()

