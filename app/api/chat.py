from fastapi import APIRouter, Depends
from pydantic import BaseModel

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
async def chat(
    request: OldChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    response = await service.chat(request.message)
    return {"response": response}


# @router.post("/v1/chat/completions")
# async def chat(req: ChatRequest):
#     global retriever

#     query = req.messages[-1].content

#     if retriever is None:
#         if any(k in query.lower() for k in ["prospektus", "saham", "laporan", "risiko"]):
#             print("🧠 Loading RAG engine...")
#             from RAG.rag_setup import setup_rag
#             retriever = setup_rag()
#             print("✅ RAG loaded")

#     answer = langchain_router(query, retriever, model)

#     return {
#         "choices": [
#             {
#                 "message": {
#                     "role": "assistant",
#                     "content": answer
#                 }
#             }
#         ]
#     }
