from app.infrastructure.llm.base import LLMProvider
from app.infrastructure.rag.rag_pipeline import RAGEngine
from app.infrastructure.mcp.mcp_manager import MCPManager
from app.services.orchestrator import Orchestrator
from app.services.resolver import Resolver
from app.services.extractors import Extractor

class ChatService:
    def __init__(self, llm: LLMProvider, rag: RAGEngine, mcp_manager: MCPManager, resolver: Resolver):
        self.llm = llm
        self.extractor = Extractor(llm)
        self.orchestrator = Orchestrator(llm, rag, mcp_manager, resolver, self.extractor)

    async def old_chat(self, user_query: str) -> str:
        # 1. RAG Step: retrieve context from your tourism dataset
        # context = await self.rag_engine.search(user_query)

        # 2. MCP Step: Get real-time data if needed

        # 3. Combine into a prompt
        messages = [{"role": "user", "content": user_query}]

        return await self.llm.generate(messages)

    async def chat(self, query: str) -> str:
        return await self.orchestrator.handle(query)
