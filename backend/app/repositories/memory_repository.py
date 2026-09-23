from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.database import Database, db


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


class MemoryRepository:
    def __init__(self, database: Database = db) -> None:
        self.db = database

    @staticmethod
    def _map(row: Any) -> dict[str, Any]:
        item = dict(row)
        item["tags"] = json.loads(item.pop("tags_json") or "[]")
        item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
        return item

    def create(self, data: dict[str, Any], supersedes: str | None = None) -> dict[str, Any]:
        memory_id = str(uuid4())
        now = utcnow()
        with self.db.transaction() as connection:
            if supersedes:
                connection.execute(
                    "UPDATE memories SET status='superseded', effective_until=?, updated_at=? WHERE id=?",
                    (now, now, supersedes),
                )
            connection.execute(
                """INSERT INTO memories (
                    id,memory_type,title,content,normalized_fact,entity,property_key,category,
                    tags_json,source_type,source_id,project_id,created_at,updated_at,effective_from,
                    importance_score,confidence_score,status,supersedes_memory_id,metadata_json
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    memory_id, data.get("memory_type", "semantic"), data["title"], data["content"],
                    data.get("normalized_fact", data["content"]), data.get("entity"), data.get("property_key"),
                    data.get("category"), json.dumps(data.get("tags", [])), data.get("source_type", "manual"),
                    data.get("source_id"), data.get("project_id"), now, now,
                    data.get("effective_from") or now, data.get("importance_score", 0.6),
                    data.get("confidence_score", 0.9), data.get("status", "current"), supersedes,
                    json.dumps(data.get("metadata", {})),
                ),
            )
            connection.execute(
                "INSERT INTO memories_fts(memory_id,title,content,normalized_fact,entity,tags) VALUES (?,?,?,?,?,?)",
                (memory_id, data["title"], data["content"], data.get("normalized_fact", data["content"]),
                 data.get("entity") or "", " ".join(data.get("tags", []))),
            )
        return self.get(memory_id)

    def get(self, memory_id: str) -> dict[str, Any]:
        with self.db.connect() as connection:
            row = connection.execute("SELECT * FROM memories WHERE id=?", (memory_id,)).fetchone()
        if not row:
            raise KeyError(memory_id)
        return self._map(row)

    def list(self, *, status: str | None = None, memory_type: str | None = None,
             project_id: str | None = None, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        clauses = ["1=1"]
        values: list[Any] = []
        if status and status != "all":
            clauses.append("status=?")
            values.append(status)
        else:
            clauses.append("status!='deleted'")
        if memory_type:
            clauses.append("memory_type=?")
            values.append(memory_type)
        if project_id:
            clauses.append("project_id=?")
            values.append(project_id)
        values.extend([limit, offset])
        with self.db.connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM memories WHERE {' AND '.join(clauses)} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                values,
            ).fetchall()
        return [self._map(row) for row in rows]

    def find_current(self, entity: str | None, property_key: str | None) -> dict[str, Any] | None:
        if not entity or not property_key:
            return None
        with self.db.connect() as connection:
            row = connection.execute(
                """SELECT * FROM memories WHERE lower(entity)=lower(?) AND property_key=?
                   AND status='current' ORDER BY updated_at DESC LIMIT 1""",
                (entity, property_key),
            ).fetchone()
        return self._map(row) if row else None

    def patch(self, memory_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        current = self.get(memory_id)
        allowed = {"title", "content", "memory_type", "category", "project_id", "importance_score", "status"}
        normalized = {key: value for key, value in changes.items() if key in allowed and value is not None}
        if changes.get("tags") is not None:
            normalized["tags_json"] = json.dumps(changes["tags"])
        if not normalized:
            return current
        normalized["updated_at"] = utcnow()
        with self.db.transaction() as connection:
            connection.execute(
                "INSERT INTO memory_versions(id,memory_id,snapshot_json) VALUES (?,?,?)",
                (str(uuid4()), memory_id, json.dumps(current, default=str)),
            )
            assignments = ",".join(f"{key}=?" for key in normalized)
            connection.execute(
                f"UPDATE memories SET {assignments} WHERE id=?", (*normalized.values(), memory_id)
            )
            if "title" in normalized or "content" in normalized or "tags_json" in normalized:
                connection.execute("DELETE FROM memories_fts WHERE memory_id=?", (memory_id,))
                refreshed = connection.execute("SELECT * FROM memories WHERE id=?", (memory_id,)).fetchone()
                connection.execute(
                    "INSERT INTO memories_fts(memory_id,title,content,normalized_fact,entity,tags) VALUES (?,?,?,?,?,?)",
                    (memory_id, refreshed["title"], refreshed["content"], refreshed["normalized_fact"],
                     refreshed["entity"] or "", refreshed["tags_json"]),
                )
        return self.get(memory_id)

    def delete(self, memory_id: str) -> None:
        self.patch(memory_id, {"status": "deleted"})

