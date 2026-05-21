from app.infrastructure.llm.base import LLMProvider
from app.infrastructure.rag.rag_pipeline import RAGEngine
from app.infrastructure.mcp.mcp_manager import MCPManager
from app.eval.batch_orchestrator import BatchOrchestrator
from app.services.resolver import Resolver


class BatchChatService:

    def __init__(
        self,
        llm: LLMProvider,
        rag: RAGEngine,
        mcp_manager: MCPManager,
        resolver: Resolver
    ):
        self.orchestrator = BatchOrchestrator(
            llm=llm,
            rag=rag,
            mcp=mcp_manager,
            resolver=resolver
        )

    async def chat(
        self,
        intent: str,
        query: str,
        row: dict
    ) -> str:

        return await self.orchestrator.handle(
            intent=intent,
            query=query,
            row=row
        )
