from pathlib import Path

from huggingface_hub import snapshot_download


root = Path(__file__).resolve().parents[1]
target = root / "backend" / "models" / "faster-whisper-tiny.en"
required = target / "model.bin"

if not required.exists():
    target.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id="Systran/faster-whisper-tiny.en",
        local_dir=target,
        allow_patterns=["config.json", "model.bin", "tokenizer.json", "vocabulary.*"],
    )

if not required.exists():
    raise RuntimeError("Whisper model download did not produce model.bin")

print(f"Voice model ready: {target}")
