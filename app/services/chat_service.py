from app.infrastructure.llm.base import LLMProvider
from app.infrastructure.rag.rag_pipeline import RAGEngine
from app.infrastructure.mcp.mcp_manager import MCPManager
from app.services.router import Router, Resolver

class ChatService:
    def __init__(self, llm: LLMProvider, rag: RAGEngine, mcp_manager: MCPManager, resolver: Resolver):
        self.llm = llm
        self.router = Router(llm=self.llm, rag=rag, mcp_manager=mcp_manager, resolver=resolver)

    async def chat(self, user_query: str) -> str:
        # 1. RAG Step: retrieve context from your tourism dataset
        # context = await self.rag_engine.search(user_query)

        # 2. MCP Step: Get real-time data if needed

        # 3. Combine into a prompt
        prompt = f"User Question: {user_query}\nAnswer:"

        return await self.llm.generate(prompt)

    async def tempchat(self, query: str) -> str:

        return await self.router.route_request(query)
