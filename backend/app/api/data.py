import json
import shutil
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.core.database import db

router = APIRouter(prefix="/data", tags=["data"])


@router.post("/export")
def export_data():
    settings = get_settings()
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    archive = settings.exports_dir / f"second-brain-export-{timestamp}.zip"
    with db.connect() as connection:
        memories = [dict(row) for row in connection.execute("SELECT * FROM memories")]
        files = [dict(row) for row in connection.execute("SELECT id,filename,title,mime_type,imported_at,status FROM files")]
    json_path = settings.exports_dir / f"metadata-{timestamp}.json"
    json_path.write_text(json.dumps({"memories": memories, "files": files}, indent=2), encoding="utf-8")
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.write(settings.database_path, "second_brain.sqlite3")
        bundle.write(json_path, "metadata.json")
        for path in settings.uploads_dir.glob("*"):
            if path.is_file():
                bundle.write(path, f"uploads/{path.name}")
    json_path.unlink(missing_ok=True)
    return FileResponse(archive, media_type="application/zip", filename=archive.name)


@router.post("/import")
def import_data(file: UploadFile = File(...)):
    settings = get_settings()
    with tempfile.TemporaryDirectory() as temp:
        archive = Path(temp) / "import.zip"
        archive.write_bytes(file.file.read())
        try:
            with zipfile.ZipFile(archive) as bundle:
                names = set(bundle.namelist())
                if "second_brain.sqlite3" not in names:
                    raise ValueError("Archive does not contain second_brain.sqlite3")
                for member in names:
                    if Path(member).is_absolute() or ".." in Path(member).parts:
                        raise ValueError("Unsafe archive path")
                backup = settings.database_path.with_suffix(".sqlite3.backup")
                if settings.database_path.exists():
                    shutil.copy2(settings.database_path, backup)
                bundle.extract("second_brain.sqlite3", temp)
                shutil.copy2(Path(temp) / "second_brain.sqlite3", settings.database_path)
                for member in names:
                    if member.startswith("uploads/") and not member.endswith("/"):
                        bundle.extract(member, temp)
                        shutil.copy2(Path(temp) / member, settings.uploads_dir / Path(member).name)
            db.migrate()
            return {"imported": True, "backup": str(backup) if backup.exists() else None}
        except Exception as exc:
            raise HTTPException(422, f"Import failed: {exc}")

