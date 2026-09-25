from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.core.database import db
from app.models.schemas import ProjectCreate, ProjectPatch
from app.services.intelligence_service import IntelligenceService

router = APIRouter(prefix="/projects", tags=["projects"])


PROJECT_SELECT = """
    SELECT p.*,
      (SELECT COUNT(*) FROM memories m WHERE m.project_id=p.id AND m.status='current') AS memory_count,
      (SELECT COUNT(*) FROM conversations c WHERE c.project_id=p.id) AS conversation_count,
      (SELECT COUNT(*) FROM tasks t WHERE t.project_id=p.id AND t.status NOT IN ('completed','done')) AS task_count,
      (SELECT COUNT(*) FROM tasks t WHERE t.project_id=p.id) AS total_task_count,
      (SELECT COUNT(*) FROM tasks t WHERE t.project_id=p.id AND t.status IN ('completed','done')) AS completed_task_count
    FROM projects p
"""


@router.get("")
def list_projects():
    with db.connect() as connection:
        projects = [dict(row) for row in connection.execute(
            PROJECT_SELECT + " ORDER BY p.updated_at DESC"
        ).fetchall()]
    for project in projects:
        project["progress"] = round(project["completed_task_count"] / max(project["total_task_count"], 1) * 100)
    return projects


@router.post("", status_code=201)
def create_project(payload: ProjectCreate):
    project_id = str(uuid4())
    now = datetime.now(UTC).isoformat()
    try:
        with db.transaction() as connection:
            connection.execute(
                "INSERT INTO projects(id,name,description,color,created_at,updated_at) VALUES (?,?,?,?,?,?)",
                (project_id, payload.name, payload.description, payload.color, now, now),
            )
            row = connection.execute(PROJECT_SELECT + " WHERE p.id=?", (project_id,)).fetchone()
        item = dict(row)
        item["progress"] = 0
        return item
    except Exception as exc:
        if "UNIQUE" in str(exc):
            raise HTTPException(409, "A project with this name already exists")
        raise


@router.get("/{project_id}")
def get_project(project_id: str):
    with db.connect() as connection:
        row = connection.execute(PROJECT_SELECT + " WHERE p.id=?", (project_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Project not found")
        memories = [dict(item) for item in connection.execute(
            """SELECT id,title,normalized_fact,memory_type,importance_score,updated_at
               FROM memories WHERE project_id=? AND status='current'
               ORDER BY updated_at DESC LIMIT 50""",
            (project_id,),
        ).fetchall()]
        conversations = [dict(item) for item in connection.execute(
            """SELECT id,title,created_at,updated_at FROM conversations
               WHERE project_id=? ORDER BY updated_at DESC LIMIT 20""",
            (project_id,),
        ).fetchall()]
        tasks = [dict(item) for item in connection.execute(
            """SELECT id,title,description,status,due_at,priority,position,parent_task_id,updated_at FROM tasks
               WHERE project_id=? ORDER BY updated_at DESC LIMIT 50""",
            (project_id,),
        ).fetchall()]
    project = dict(row)
    project["progress"] = round(project["completed_task_count"] / max(project["total_task_count"], 1) * 100)
    return {**project, "memories": memories, "conversations": conversations, "tasks": tasks,
            "resurfaced": IntelligenceService(db).resurface(project_id)}


@router.get("/{project_id}/resurface")
def resurface_project(project_id: str):
    return IntelligenceService(db).resurface(project_id)


@router.patch("/{project_id}")
def update_project(project_id: str, payload: ProjectPatch):
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not changes:
        return get_project(project_id)
    changes["updated_at"] = datetime.now(UTC).isoformat()
    assignments = ",".join(f"{key}=?" for key in changes)
    try:
        with db.transaction() as connection:
            result = connection.execute(
                f"UPDATE projects SET {assignments} WHERE id=?",
                (*changes.values(), project_id),
            )
            if result.rowcount == 0:
                raise HTTPException(404, "Project not found")
        return get_project(project_id)
    except Exception as exc:
        if "UNIQUE" in str(exc):
            raise HTTPException(409, "A project with this name already exists")
        raise


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str):
    with db.transaction() as connection:
        result = connection.execute("DELETE FROM projects WHERE id=?", (project_id,))
        if result.rowcount == 0:
            raise HTTPException(404, "Project not found")
