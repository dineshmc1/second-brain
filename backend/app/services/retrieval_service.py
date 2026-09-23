from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from app.core.database import Database, db
from app.services.embedding_service import EmbeddingService, get_embedding_service
from app.utils.text import fts_query


class RetrievalService:
    def __init__(self, database: Database = db, embeddings: EmbeddingService | None = None) -> None:
        self.db = database
        self.embeddings = embeddings or get_embedding_service()

    def search(self, query: str, *, limit: int = 8, project_id: str | None = None,
               include_history: bool | None = None) -> list[dict[str, Any]]:
        historical = include_history if include_history is not None else any(
            word in query.lower() for word in ("previous", "before", "history", "used to", "old")
        )
        ranks: dict[tuple[str, str], float] = defaultdict(float)
        results: dict[tuple[str, str], dict[str, Any]] = {}
        fts = fts_query(query)
        with self.db.connect() as connection:
            if fts:
                status_sql = "m.status!='deleted'" if historical else "m.status='current'"
                project_sql = " AND m.project_id=?" if project_id else ""
                values: list[Any] = [fts]
                if project_id:
                    values.append(project_id)
                rows = connection.execute(
                    f"""SELECT m.*, bm25(memories_fts) rank FROM memories_fts
                    JOIN memories m ON m.id=memories_fts.memory_id
                    WHERE memories_fts MATCH ? AND {status_sql}{project_sql}
                    ORDER BY rank LIMIT 30""", values,
                ).fetchall()
                for rank, row in enumerate(rows, 1):
                    key = ("memory", row["id"])
                    ranks[key] += 1 / (60 + rank)
                    results[key] = self._memory_result(row)
                chunk_rows = connection.execute(
                    """SELECT c.*, f.filename, f.title file_title, bm25(chunks_fts) rank
                    FROM chunks_fts JOIN document_chunks c ON c.id=chunks_fts.chunk_id
                    JOIN files f ON f.id=c.file_id WHERE chunks_fts MATCH ?
                    ORDER BY rank LIMIT 30""", (fts,),
                ).fetchall()
                for rank, row in enumerate(chunk_rows, 1):
                    key = ("chunk", row["id"])
                    ranks[key] += 1 / (60 + rank)
                    results[key] = self._chunk_result(row)

            query_vector = self.embeddings.embed([query])[0]
            vector_rows = connection.execute(
                """SELECT c.*, f.filename, f.title file_title FROM document_chunks c
                JOIN files f ON f.id=c.file_id WHERE c.embedding IS NOT NULL"""
            ).fetchall()
            similarities = []
            for row in vector_rows:
                vector = self.embeddings.deserialize(row["embedding"], row["embedding_dim"])
                similarities.append((self.embeddings.cosine(query_vector, vector), row))
            for rank, (similarity, row) in enumerate(sorted(similarities, key=lambda pair: pair[0], reverse=True)[:30], 1):
                if similarity <= 0:
                    continue
                key = ("chunk", row["id"])
                ranks[key] += 1 / (60 + rank)
                results.setdefault(key, self._chunk_result(row))
                results[key]["semantic_score"] = similarity

        ranked = []
        for key, item in results.items():
            freshness = 0.003 if item.get("status") == "current" else 0
            importance = float(item.get("importance_score", 0.5)) * 0.002
            item["score"] = round(ranks[key] + freshness + importance, 6)
            ranked.append(item)
        return sorted(ranked, key=lambda item: item["score"], reverse=True)[:limit]

    @staticmethod
    def _memory_result(row: Any) -> dict[str, Any]:
        return {
            "id": row["id"], "kind": "memory", "title": row["title"],
            "excerpt": row["normalized_fact"], "source_type": row["source_type"],
            "page": None, "status": row["status"], "importance_score": row["importance_score"],
            "created_at": row["created_at"], "metadata": {"entity": row["entity"], "property_key": row["property_key"]},
        }

    @staticmethod
    def _chunk_result(row: Any) -> dict[str, Any]:
        return {
            "id": row["id"], "kind": "chunk", "title": row["file_title"],
            "excerpt": row["text"][:800], "source_type": "document", "page": row["page"],
            "status": "current", "importance_score": 0.5, "file_id": row["file_id"],
            "metadata": {"filename": row["filename"], "chunk_number": row["chunk_number"]},
        }

