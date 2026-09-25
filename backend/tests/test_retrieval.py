from app.models.schemas import MemoryCreate
from app.repositories.memory_repository import MemoryRepository
from app.services.memory_service import MemoryService
from app.services.retrieval_service import RetrievalService


def test_retrieval_prefers_current_memory(database):
    repository = MemoryRepository(database)
    memories = MemoryService(repository)
    memories.remember(MemoryCreate(content="Remember that Project Atlas will launch in October."))
    current, _ = memories.remember(MemoryCreate(content="Change Project Atlas launch to December."))
    results = RetrievalService(database).search("When will Project Atlas launch?")
    assert results
    assert results[0]["id"] == current["id"]
    assert "December" in results[0]["excerpt"]


def test_historical_query_includes_superseded(database):
    repository = MemoryRepository(database)
    memories = MemoryService(repository)
    old, _ = memories.remember(MemoryCreate(content="Remember that Project Atlas will launch in October."))
    memories.remember(MemoryCreate(content="Change Project Atlas launch to December."))
    results = RetrievalService(database).search("What was the previous Project Atlas launch?")
    assert any(item["id"] == old["id"] and item["status"] == "superseded" for item in results)


def test_unknown_query_returns_no_personal_memory(database):
    results = RetrievalService(database).search("What is my favorite telescope?")
    assert results == []


def test_project_search_excludes_other_projects(database):
    from datetime import UTC, datetime

    now = datetime.now(UTC).isoformat()
    with database.transaction() as connection:
        connection.execute(
            "INSERT INTO projects(id,name,description,color,created_at,updated_at) VALUES (?,?,?,?,?,?)",
            ("atlas", "Atlas", "", "#68e8ff", now, now),
        )
        connection.execute(
            "INSERT INTO projects(id,name,description,color,created_at,updated_at) VALUES (?,?,?,?,?,?)",
            ("apollo", "Apollo", "", "#68e8ff", now, now),
        )
    memories = MemoryService(MemoryRepository(database))
    atlas, _ = memories.remember(MemoryCreate(content="Remember that the launch color is cyan.", project_id="atlas"))
    apollo, _ = memories.remember(MemoryCreate(content="Remember that the launch color is amber.", project_id="apollo"))

    results = RetrievalService(database).search("What is the launch color?", project_id="atlas")

    assert any(item["id"] == atlas["id"] for item in results)
    assert all(item["id"] != apollo["id"] for item in results)
