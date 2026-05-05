from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.chat import router
from app.infrastructure.llm.llm_factory import create_llm_provider
from app.services.chat_service import ChatService
from app.infrastructure.rag.rag_pipeline import RAGEngine
from app.infrastructure.mcp.mcp_manager import MCPManager
from app.services.resolver import Resolver


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create LLM via factory
    llm = create_llm_provider()
    rag_engine = RAGEngine()
    mcp_manager = MCPManager()
    resolver = Resolver()

    # Inject into app state
    app.state.chat_service = ChatService(
        llm=llm, rag=rag_engine, mcp_manager=mcp_manager, resolver=resolver)

    yield

    # Optional cleanup here later


# Create FastAPI app
app = FastAPI(lifespan=lifespan)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# Register routes
app.include_router(router)
