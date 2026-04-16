from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

from app.api.chat import router
from app.infrastructure.llm.llm_factory import create_llm_provider
from app.services.chat_service import ChatService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create LLM via factory
    llm = create_llm_provider()

    # Inject into app state
    app.state.chat_service = ChatService(llm=llm)

    yield

    # Optional cleanup here later


# Create FastAPI app
app = FastAPI(lifespan=lifespan)

# Register routes
app.include_router(router)
