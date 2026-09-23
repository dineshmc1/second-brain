from __future__ import annotations

import mimetypes
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from app.core.config import get_settings
from app.core.database import Database, db
from app.services.embedding_service import EmbeddingService, get_embedding_service
from app.utils.text import semantic_chunks


class UnsupportedFileError(ValueError):
    pass


class IngestionService:
    SUPPORTED = {".pdf", ".txt", ".md", ".markdown", ".docx", ".png", ".jpg", ".jpeg", ".webp"}

    def __init__(self, database: Database = db, embeddings: EmbeddingService | None = None) -> None:
        self.db = database
        self.embeddings = embeddings or get_embedding_service()
        self.settings = get_settings()

    def ingest(self, filename: str, stream: BinaryIO, content_type: str | None = None) -> dict:
        safe_name = Path(filename).name
        suffix = Path(safe_name).suffix.lower()
        if suffix not in self.SUPPORTED:
            raise UnsupportedFileError(f"Unsupported file type: {suffix or 'unknown'}")
        file_id = str(uuid4())
        destination = self.settings.uploads_dir / f"{file_id}{suffix}"
        with destination.open("wb") as output:
            shutil.copyfileobj(stream, output)
        mime = content_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
        imported_at = datetime.now(UTC).isoformat()
        try:
            pages = self._extract(destination, suffix)
            all_chunks: list[tuple[int | None, int, str]] = []
            chunk_number = 0
            for page_number, text in pages:
                for chunk in semantic_chunks(text):
                    all_chunks.append((page_number, chunk_number, chunk))
                    chunk_number += 1
            vectors = self.embeddings.embed([item[2] for item in all_chunks]) if all_chunks else []
            with self.db.transaction() as connection:
                connection.execute(
                    """INSERT INTO files(id,filename,filepath,title,mime_type,size_bytes,page_count,imported_at,status)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (file_id, safe_name, str(destination), Path(safe_name).stem, mime,
                     destination.stat().st_size, len(pages) or None, imported_at, "ready"),
                )
                for (page, number, text), vector in zip(all_chunks, vectors, strict=True):
                    chunk_id = str(uuid4())
                    connection.execute(
                        """INSERT INTO document_chunks(id,file_id,page,chunk_number,text,embedding,embedding_dim)
                        VALUES (?,?,?,?,?,?,?)""",
                        (chunk_id, file_id, page, number, text, self.embeddings.serialize(vector), len(vector)),
                    )
                    connection.execute("INSERT INTO chunks_fts(chunk_id,text) VALUES (?,?)", (chunk_id, text))
                    connection.execute(
                        "INSERT INTO embedding_metadata(owner_type,owner_id,model,dimensions) VALUES (?,?,?,?)",
                        ("chunk", chunk_id, self.embeddings.model_name, len(vector)),
                    )
            return self.get_file(file_id)
        except Exception as exc:
            with self.db.transaction() as connection:
                connection.execute(
                    """INSERT OR REPLACE INTO files(id,filename,filepath,title,mime_type,size_bytes,imported_at,status,error)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (file_id, safe_name, str(destination), Path(safe_name).stem, mime,
                     destination.stat().st_size, imported_at, "failed", str(exc)[:1000]),
                )
            raise

    def _extract(self, path: Path, suffix: str) -> list[tuple[int | None, str]]:
        if suffix == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(path)
            return [(index + 1, page.extract_text() or "") for index, page in enumerate(reader.pages)]
        if suffix == ".docx":
            from docx import Document

            document = Document(path)
            return [(None, "\n".join(paragraph.text for paragraph in document.paragraphs))]
        if suffix in {".txt", ".md", ".markdown"}:
            return [(None, path.read_text(encoding="utf-8", errors="replace"))]
        try:
            import pytesseract
            from PIL import Image

            return [(None, pytesseract.image_to_string(Image.open(path)))]
        except Exception:
            return [(None, "")]

    def get_file(self, file_id: str) -> dict:
        with self.db.connect() as connection:
            row = connection.execute(
                """SELECT f.*, COUNT(c.id) chunk_count FROM files f
                LEFT JOIN document_chunks c ON c.file_id=f.id WHERE f.id=? GROUP BY f.id""", (file_id,)
            ).fetchone()
        if not row:
            raise KeyError(file_id)
        result = dict(row)
        result.pop("filepath", None)
        return result

    def list_files(self) -> list[dict]:
        with self.db.connect() as connection:
            rows = connection.execute(
                """SELECT f.*, COUNT(c.id) chunk_count FROM files f
                LEFT JOIN document_chunks c ON c.file_id=f.id GROUP BY f.id ORDER BY f.imported_at DESC"""
            ).fetchall()
        results = []
        for row in rows:
            item = dict(row)
            item.pop("filepath", None)
            results.append(item)
        return results

