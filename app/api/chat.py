from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional

from app.core.dependencies import get_chat_service
from app.services.chat_service import ChatService

router = APIRouter()


class OldChatRequest(BaseModel):
    message: str


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: Optional[str] = "qwen-local"
    messages: List[Message]


@router.get("/")
async def root():
    return {"message": "Backend is running 🚀"}


@router.get("/hi")
async def hi():
    return {"message": "Hello World"}


@router.post("/chat")
async def old_chat(
    request: OldChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    response = await service.old_chat(request.message)
    return {"response": response}


@router.post("/v1/chat/completions")
async def chat(req: ChatRequest, service: ChatService = Depends(get_chat_service)):
    query = req.messages[-1].content

    answer = await service.chat(query)

    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": answer
                }
            }
        ]
    }
