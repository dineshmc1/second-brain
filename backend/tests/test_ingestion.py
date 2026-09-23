from io import BytesIO

import pytest

from app.services.ingestion_service import IngestionService, UnsupportedFileError


def test_text_ingestion_creates_searchable_chunks(database, monkeypatch, tmp_path):
    service = IngestionService(database)
    service.settings.data_dir = tmp_path
    service.settings.uploads_dir.mkdir()
    result = service.ingest("notes.txt", BytesIO(b"Transformers use self-attention for contextual representations."), "text/plain")
    assert result["status"] == "ready"
    assert result["chunk_count"] == 1


def test_unsupported_file_fails_cleanly(database):
    service = IngestionService(database)
    with pytest.raises(UnsupportedFileError):
        service.ingest("archive.exe", BytesIO(b"bad"))
