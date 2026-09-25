from fastapi import APIRouter, HTTPException

from app.services.calendar_service import CalendarService
from app.services.intelligence_service import IntelligenceService

router = APIRouter(prefix="/intelligence", tags=["intelligence"])
service = IntelligenceService()


@router.get("/overview")
def overview():
    return service.overview()


@router.get("/memory-health")
def memory_health():
    return service.memory_health()


@router.get("/cognitive-twin")
def cognitive_twin():
    return service.cognitive_twin()


@router.get("/genome")
def knowledge_genome():
    return service.genome()


@router.get("/calendar")
def calendar(days: int = 7):
    try:
        return {"events": CalendarService().upcoming(min(max(days, 1), 31))}
    except Exception as exc:
        raise HTTPException(422, str(exc))

