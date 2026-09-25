from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query

from app.core.database import db
from app.models.schemas import TaskBreakdown, TaskCreate, TaskPatch
from app.services.llm_service import LLMUnavailable, get_llm_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


TASK_SELECT = """SELECT t.*,p.name project_name,p.color project_color FROM tasks t
LEFT JOIN projects p ON p.id=t.project_id"""


def _map(row):
    item = dict(row)
    if item["status"] in {"open", "todo"}:
        item["status"] = "backlog"
    elif item["status"] == "completed":
        item["status"] = "done"
    return item


@router.get("")
def list_tasks(project_id: str | None = None):
    clause, values = (" WHERE t.project_id=?", (project_id,)) if project_id else ("", ())
    with db.connect() as connection:
        rows = connection.execute(
            TASK_SELECT + clause + " ORDER BY t.status,t.position,t.created_at DESC", values
        ).fetchall()
    return [_map(row) for row in rows]


@router.post("", status_code=201)
def create_task(payload: TaskCreate):
    task_id = str(uuid4())
    now = datetime.now(UTC).isoformat()
    with db.transaction() as connection:
        position = connection.execute(
            "SELECT COALESCE(MAX(position),-1)+1 FROM tasks WHERE status=?", (payload.status,)
        ).fetchone()[0]
        connection.execute(
            """INSERT INTO tasks(id,title,description,status,due_at,project_id,source_memory_id,created_at,updated_at,priority,position,parent_task_id,completed_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (task_id, payload.title, payload.description, payload.status,
             payload.due_at.isoformat() if payload.due_at else None, payload.project_id, None, now, now,
             payload.priority, position, payload.parent_task_id, now if payload.status == "done" else None),
        )
        row = connection.execute(TASK_SELECT + " WHERE t.id=?", (task_id,)).fetchone()
    return _map(row)


@router.patch("/{task_id}")
def patch_task(task_id: str, payload: TaskPatch):
    changes = payload.model_dump(exclude_unset=True)
    if "due_at" in changes and changes["due_at"] is not None:
        changes["due_at"] = changes["due_at"].isoformat()
    if changes.get("status") == "done":
        changes["completed_at"] = datetime.now(UTC).isoformat()
    elif "status" in changes:
        changes["completed_at"] = None
    changes["updated_at"] = datetime.now(UTC).isoformat()
    with db.transaction() as connection:
        assignments = ",".join(f"{key}=?" for key in changes)
        result = connection.execute(f"UPDATE tasks SET {assignments} WHERE id=?", (*changes.values(), task_id))
        if result.rowcount == 0:
            raise HTTPException(404, "Task not found")
        row = connection.execute(TASK_SELECT + " WHERE t.id=?", (task_id,)).fetchone()
    return _map(row)


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: str):
    with db.transaction() as connection:
        result = connection.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        if result.rowcount == 0:
            raise HTTPException(404, "Task not found")


@router.post("/breakdown")
def breakdown(payload: TaskBreakdown):
    prompt = (
        f"Complex task: {payload.title}\n"
        "Break it into 4-7 concrete, independently completable cards. Output only one card per line. "
        "Each line: short title | definition of done."
    )
    ai_used = False
    try:
        response = get_llm_service().compact_response(
            "task_breakdown", "You convert complex outcomes into minimal executable steps. Avoid vague planning tasks.", prompt, 360
        )
        parsed = []
        for line in response["text"].splitlines():
            clean = re.sub(r"^\s*[-*\d.)]+\s*", "", line).strip()
            if "|" in clean:
                title, description = [part.strip() for part in clean.split("|", 1)]
                if title:
                    parsed.append((title[:240], description[:1000]))
        ai_used = len(parsed) >= 3
    except LLMUnavailable:
        parsed = []
    if not parsed:
        parsed = [
            ("Define the outcome", f"Write the measurable definition of done for: {payload.title}"),
            ("Gather constraints", "List required inputs, dependencies, deadlines, and limitations."),
            ("Build the smallest first version", "Produce the smallest end-to-end result that can be evaluated."),
            ("Test the result", "Check the output against the definition of done and record failures."),
            ("Refine and finish", "Fix the highest-impact gaps and complete the deliverable."),
        ]
    cards = []
    parent = create_task(TaskCreate(title=payload.title[:240], project_id=payload.project_id, priority="high", status="backlog"))
    for title, description in parsed[:7]:
        cards.append(create_task(TaskCreate(
            title=title, description=description, project_id=payload.project_id,
            parent_task_id=parent["id"], status="backlog",
        )))
    return {"parent": parent, "cards": cards, "ai_used": ai_used}


@router.post("/organize")
def organize(project_id: str | None = Query(default=None)):
    clause, values = (" AND project_id=?", [project_id]) if project_id else ("", [])
    with db.transaction() as connection:
        rows = connection.execute(
            """SELECT id,status,priority,due_at FROM tasks WHERE status NOT IN ('done','completed','blocked')""" + clause,
            values,
        ).fetchall()
        ranked = sorted(rows, key=lambda row: (
            {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(row["priority"], 2),
            row["due_at"] is None, row["due_at"] or "9999",
        ))
        for index, row in enumerate(ranked):
            status = "next" if index < 3 else ("in_progress" if row["status"] == "in_progress" else "backlog")
            connection.execute(
                "UPDATE tasks SET status=?,position=?,updated_at=? WHERE id=?",
                (status, index, datetime.now(UTC).isoformat(), row["id"]),
            )
    return {"organized": len(ranked), "strategy": "priority, due date, then focus limit of three Next cards"}

