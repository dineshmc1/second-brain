from fastapi import APIRouter

from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])
service = ChatService()


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest):
    return service.respond(payload)

