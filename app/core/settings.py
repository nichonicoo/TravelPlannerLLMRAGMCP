import os
from dotenv import load_dotenv
from langfuse import get_client
from pathlib import Path

load_dotenv()
langfuse = get_client()


class Settings:
    """Application settings with environment variables."""
    # Project root directory
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    EVALS_DIR = PROJECT_ROOT / "evals"

    LLM_GENERATION_MODE = os.getenv("LLM_GENERATION_MODE", "benchmark")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "hf")

    # hf config
    HF_MODEL_NAME = os.getenv("HF_MODEL_NAME", "distilgpt2")
    HF_ADAPTER_NAME = os.getenv("HF_ADAPTER_NAME")
    HF_TOKEN = os.getenv("HF_TOKEN")

    # openai config
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")

    # lmstudio config
    LMSTUDIO_MODEL_NAME = os.getenv("LMSTUDIO_MODEL_NAME", "")
    LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "")

    # serpapi config
    SERP_API_KEY = os.getenv("SERP_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    @property
    def LMSTUDIO_TEMPERATURE(self) -> float:
        """Safely parses and returns the LM Studio temperature fallback to 0.0."""
        raw_temp = os.getenv("LMSTUDIO_TEMPERATURE")
        if raw_temp and raw_temp.strip():
            try:
                return float(raw_temp)
            except ValueError:
                pass
        return 0.0


settings = Settings()
