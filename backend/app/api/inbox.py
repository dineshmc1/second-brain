from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.core.database import db
from app.models.schemas import InboxCreate, InboxProcess, MemoryCreate
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/inbox", tags=["inbox"])


def _suggest(content: str) -> str:
    lowered = content.lower()
    if re.search(r"\b(todo|need to|must|follow up|deadline|task)\b", lowered):
        return "task"
    if re.search(r"\b(project|initiative|build|launch)\b", lowered) and len(content) < 300:
        return "project"
    return "memory"


@router.get("")
def list_inbox(status: str = "unprocessed"):
    with db.connect() as connection:
        rows = connection.execute(
            "SELECT * FROM inbox_items WHERE status=? ORDER BY created_at DESC LIMIT 250", (status,)
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
        result.append(item)
    return result


@router.post("", status_code=201)
def capture(payload: InboxCreate):
    item_id = str(uuid4())
    now = datetime.now(UTC).isoformat()
    suggestion = _suggest(payload.content)
    with db.transaction() as connection:
        connection.execute(
            "INSERT INTO inbox_items(id,content,source_type,status,suggested_type,metadata_json,created_at) VALUES (?,?,?,?,?,?,?)",
            (item_id, payload.content.strip(), payload.source_type, "unprocessed", suggestion, "{}", now),
        )
    return {"id": item_id, "content": payload.content.strip(), "source_type": payload.source_type,
            "status": "unprocessed", "suggested_type": suggestion, "metadata": {}, "created_at": now}


@router.post("/{item_id}/process")
def process(item_id: str, payload: InboxProcess):
    with db.connect() as connection:
        row = connection.execute("SELECT * FROM inbox_items WHERE id=?", (item_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Inbox item not found")
    content = row["content"]
    result = None
    if payload.action == "memory":
        result, _ = MemoryService().remember(MemoryCreate(content=content, project_id=payload.project_id, source_type="inbox"))
    elif payload.action == "task":
        now = datetime.now(UTC).isoformat()
        task_id = str(uuid4())
        with db.transaction() as connection:
            connection.execute(
                """INSERT INTO tasks(id,title,description,status,due_at,project_id,created_at,updated_at,priority,position)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (task_id, content[:240], content if len(content) > 240 else "", "backlog", None, payload.project_id, now, now, "medium", 0),
            )
        result = {"id": task_id, "title": content[:240]}
    elif payload.action == "project":
        project_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        try:
            with db.transaction() as connection:
                connection.execute(
                    "INSERT INTO projects(id,name,description,color,created_at,updated_at,goal,status) VALUES (?,?,?,?,?,?,?,?)",
                    (project_id, content[:120], "Created from Smart Inbox", "#68e8ff", now, now, content, "active"),
                )
            result = {"id": project_id, "name": content[:120]}
        except Exception as exc:
            if "UNIQUE" in str(exc):
                raise HTTPException(409, "A project with this name already exists")
            raise
    status = "discarded" if payload.action == "discard" else "processed"
    with db.transaction() as connection:
        connection.execute(
            "UPDATE inbox_items SET status=?,processed_at=? WHERE id=?",
            (status, datetime.now(UTC).isoformat(), item_id),
        )
    return {"processed": True, "action": payload.action, "result": result}

