from app.api import projects as projects_api
from app.models.schemas import MemoryCreate, ProjectCreate, ProjectPatch
from app.repositories.memory_repository import MemoryRepository
from app.services.memory_service import MemoryService


def test_project_workspace_lifecycle(database, monkeypatch):
    monkeypatch.setattr(projects_api, "db", database)
    project = projects_api.create_project(ProjectCreate(name="Atlas", description="Launch work"))
    project_id = project["id"]

    MemoryService(MemoryRepository(database)).remember(
        MemoryCreate(content="Remember that Project Atlas launches in October.", project_id=project_id)
    )

    detail = projects_api.get_project(project_id)
    assert detail["memory_count"] == 1
    assert "October" in detail["memories"][0]["normalized_fact"]

    updated = projects_api.update_project(
        project_id, ProjectPatch(name="Atlas Launch", description="Updated workspace", color="#112233")
    )
    assert updated["name"] == "Atlas Launch"
    assert updated["color"] == "#112233"
    assert projects_api.list_projects()[0]["memory_count"] == 1

    projects_api.delete_project(project_id)
    assert MemoryRepository(database).list(status="current")[0]["project_id"] is None
