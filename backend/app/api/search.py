from fastapi import APIRouter, Query

from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/search", tags=["search"])
service = RetrievalService()


@router.get("")
def search(q: str = Query(min_length=1), limit: int = Query(20, le=100),
           project_id: str | None = None, include_history: bool | None = None):
    return service.search(q, limit=limit, project_id=project_id, include_history=include_history)

