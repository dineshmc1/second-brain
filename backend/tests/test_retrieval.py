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

