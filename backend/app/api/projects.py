from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.core.database import db
from app.models.schemas import ProjectCreate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
def list_projects():
    with db.connect() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM projects ORDER BY updated_at DESC"
        ).fetchall()]


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
            row = connection.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        return dict(row)
    except Exception as exc:
        if "UNIQUE" in str(exc):
            raise HTTPException(409, "A project with this name already exists")
        raise

