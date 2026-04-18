# from RAG.rag_setup import setup_rag
from LLM.gemini_model import model

# from router.langchain_router import langchain_router
from router.router import langchain_router

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from langfuse import get_client, observe

langfuse = get_client()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Data Model OpenAI Style
class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: Optional[str] = "qwen-local"
    messages: List[Message]


# helper format conversation
def format_messages(messages: List[Message]) -> str:
    text = ""
    for m in messages:
        if m.role == "user":
            text += f"User: {m.content}\n"
        elif m.role == "assistant":
            text += f"Assistant: {m.content}\n"
        elif m.role == "system":
            text += f"System: {m.content}\n"
    return text


def generate_response(prompt: str) -> str:
    # 👉 nanti ganti dengan Qwen / LangChain
    return f"🤖 AI Response:\n{prompt[-200:]}"


# =========================
# ENDPOINT: CHAT (WAJIB)
# =========================
@app.post("/v1/chat/completions")
@observe(name="chat_endpoint")
async def chat(req: ChatRequest):
    global retriever

    query = req.messages[-1].content

    if retriever is None:
        if any(
            k in query.lower() for k in ["prospektus", "saham", "laporan", "risiko"]
        ):
            print("🧠 Loading RAG engine...")
            from RAG.rag_setup import setup_rag

            retriever = setup_rag()
            print("✅ RAG loaded")

    answer = langchain_router(query, retriever, model)

    return {"choices": [{"message": {"role": "assistant", "content": answer}}]}


# =========================
# ENDPOINT: MODELS (WAJIB)
# =========================
@app.get("/v1/models")
async def get_models():
    return {
        "object": "list",
        "data": [{"id": "qwen-local", "object": "model", "owned_by": "you"}],
    }


# =========================
# ROOT (optional)
# =========================
@app.get("/")
async def root():
    return {"message": "Backend is running 🚀"}


retriever = None

# print("🔥 Ready!")
# print("Ketik 'exit' untuk keluar.\n")

# while True:
#     query = input("user: ")

#     if query == 'exit':
#         break

#     if retriever is None:
#         # heuristik murah: keyword RAG
#         if any(k in query.lower() for k in ["prospektus", "saham", "laporan", "risiko"]):
#             print("🧠 Loading RAG engine...")
#             from RAG.rag_setup import setup_rag
#             retriever = setup_rag()
#             print("✅ RAG loaded")

#     answer = langchain_router(query, retriever, model)
#     print("Bot:", answer)

# INIT RAG
# retriever = setup_rag()

# print("\n🔍 DEBUG: Testing retriever untuk query 'kantor pusat'")
# retrieved_docs = retriever.invoke("kantor pusat")

# for d in retrieved_docs:
#     print("\n----- CHUNK -----")
#     print("HALAMAN:", d.metadata.get("page"))
#     print(d.page_content[:400], "...")
#     print("-----------------\n")

# print("🔥 DEBUG DONE — lanjut chatbot…\n")

# print("🔥 AI Stock Assistant ready!")
# print("Ketik 'exit' untuk keluar.\n")

# while True:
#     query = input("User: ")

#     if query == "exit":
#         break

#     answer = langchain_router(query, retriever, model)
#     print("Bot:", answer)
