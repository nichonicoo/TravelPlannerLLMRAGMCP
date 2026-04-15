from app.infrastructure.llm.base import LLMProvider


class ChatService:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def chat(self, user_query: str) -> str:
        # 1. RAG Step: retrieve context from your tourism dataset
        # context = await self.rag_engine.search(user_query)

        # 2. MCP Step: Get real-time data if needed

        # 3. Combine into a prompt
        prompt = f"User Question: {user_query}\nAnswer:"

        return await self.llm.generate(prompt)
