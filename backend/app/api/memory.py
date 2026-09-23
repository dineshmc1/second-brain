from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import MemoryCreate, MemoryOut, MemoryPatch
from app.repositories.memory_repository import MemoryRepository
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/memories", tags=["memories"])
repository = MemoryRepository()
service = MemoryService(repository)


@router.get("")
def list_memories(status: str = "current", memory_type: str | None = None,
                  project_id: str | None = None, limit: int = Query(100, le=500)):
    return repository.list(status=status, memory_type=memory_type, project_id=project_id, limit=limit)


@router.post("", status_code=201)
def create_memory(payload: MemoryCreate):
    memory, operation = service.remember(payload)
    return {"memory": memory, "operation": operation}


@router.get("/{memory_id}")
def get_memory(memory_id: str):
    try:
        return repository.get(memory_id)
    except KeyError:
        raise HTTPException(404, "Memory not found")


@router.patch("/{memory_id}")
def update_memory(memory_id: str, payload: MemoryPatch):
    try:
        return repository.patch(memory_id, payload.model_dump(exclude_unset=True))
    except KeyError:
        raise HTTPException(404, "Memory not found")


@router.delete("/{memory_id}", status_code=204)
def delete_memory(memory_id: str):
    try:
        repository.delete(memory_id)
    except KeyError:
        raise HTTPException(404, "Memory not found")

