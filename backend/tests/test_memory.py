from app.models.schemas import MemoryCreate
from app.repositories.memory_repository import MemoryRepository
from app.services.memory_service import MemoryService


def test_memory_creation(database):
    service = MemoryService(MemoryRepository(database))
    memory, operation = service.remember(MemoryCreate(content="Remember that Project Atlas will launch in October."))
    assert operation == "CREATE"
    assert memory["entity"] == "Project Atlas"
    assert "October" in memory["normalized_fact"]
    assert memory["status"] == "current"


def test_update_supersedes_and_preserves_history(database):
    repository = MemoryRepository(database)
    service = MemoryService(repository)
    old, _ = service.remember(MemoryCreate(content="Remember that Project Atlas will launch in October."))
    new, operation = service.remember(MemoryCreate(content="Change Project Atlas launch to December."))
    assert operation == "SUPERSEDE"
    assert new["supersedes_memory_id"] == old["id"]
    assert repository.get(old["id"])["status"] == "superseded"
    assert "December" in new["normalized_fact"]


def test_duplicate_confirms_existing_memory(database):
    service = MemoryService(MemoryRepository(database))
    first, _ = service.remember(MemoryCreate(content="Remember that Project Atlas will launch in October."))
    second, operation = service.remember(MemoryCreate(content="Remember that Project Atlas will launch in October."))
    assert operation == "CONFIRM"
    assert first["id"] == second["id"]


def test_patch_creates_version(database):
    repository = MemoryRepository(database)
    memory = repository.create({"title": "A fact", "content": "old", "normalized_fact": "old"})
    updated = repository.patch(memory["id"], {"title": "Edited fact", "content": "new", "tags": ["edited"]})
    assert updated["title"] == "Edited fact"
    assert updated["content"] == "new"
    assert updated["normalized_fact"] == "new"
    assert updated["tags"] == ["edited"]
    with database.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM memory_versions").fetchone()[0] == 1
        indexed = connection.execute(
            "SELECT normalized_fact FROM memories_fts WHERE memory_id=?", (memory["id"],)
        ).fetchone()
        assert indexed[0] == "new"
