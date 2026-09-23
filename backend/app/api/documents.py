from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.ingestion_service import IngestionService, UnsupportedFileError

router = APIRouter(prefix="/files", tags=["files"])
service = IngestionService()


@router.get("")
def list_files():
    return service.list_files()


@router.post("", status_code=201)
def upload_file(file: UploadFile = File(...)):
    try:
        return service.ingest(file.filename or "upload", file.file, file.content_type)
    except UnsupportedFileError as exc:
        raise HTTPException(415, str(exc))
    except Exception as exc:
        raise HTTPException(422, f"Could not process file: {exc}")

