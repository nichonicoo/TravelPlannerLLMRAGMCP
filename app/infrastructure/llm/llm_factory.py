from app.infrastructure.llm.providers.hf_provider import HuggingFaceLocal
from app.infrastructure.llm.providers.openai_provider import OpenAICompatibleProvider
from app.infrastructure.llm.providers.lmstudio_provider import LMStudioProvider
from app.core.settings import settings
from app.infrastructure.llm.base import LLMProvider


def create_llm_provider() -> LLMProvider:
    if settings.LLM_PROVIDER == "hf":
        return HuggingFaceLocal(
            model_id=settings.HF_MODEL_NAME, token=settings.HF_TOKEN
        )
    elif settings.LLM_PROVIDER == "openai":
        return OpenAICompatibleProvider(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            model_id=settings.OPENAI_MODEL_NAME,
        )
    elif settings.LLM_PROVIDER == "lmstudio":
        return LMStudioProvider(
            model_id=settings.LMSTUDIO_MODEL_NAME,
            base_url=settings.LMSTUDIO_BASE_URL,
            temperature=settings.LMSTUDIO_TEMPERATURE,
        )
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {settings.LLM_PROVIDER}")
