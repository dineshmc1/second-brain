from fastapi import APIRouter, HTTPException

from app.models.schemas import LearningGoalCreate, LearningNodePatch, LearningRun
from app.services.learning_service import LearningService

router = APIRouter(prefix="/learning", tags=["learning"])
service = LearningService()


@router.get("/goals")
def goals():
    return service.goals()


@router.post("/goals", status_code=201)
def create_goal(payload: LearningGoalCreate):
    return service.create_goal(payload)


@router.patch("/nodes/{node_id}")
def patch_node(node_id: str, payload: LearningNodePatch):
    try:
        return service.patch_node(node_id, payload.model_dump(exclude_unset=True))
    except KeyError:
        raise HTTPException(404, "Learning node not found")


@router.post("/run")
def run(payload: LearningRun):
    return service.run(payload)


@router.get("/usage")
def usage():
    return service.usage()

