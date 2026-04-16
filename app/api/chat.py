from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.dependencies import get_chat_service
from app.services.chat_service import ChatService

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.get("/hi")
async def hi():
    return {"message": "Hello World"}


@router.post("/chat")
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    response = await service.chat(request.message)
    return {"response": response}
