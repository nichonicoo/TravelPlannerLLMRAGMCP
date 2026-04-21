import os
from dotenv import load_dotenv
from langfuse import get_client

load_dotenv()
langfuse = get_client()


class Settings:
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "hf")

    # hf config
    HF_MODEL_NAME = os.getenv("HF_MODEL_NAME", "distilgpt2")
    HF_TOKEN = os.getenv("HF_TOKEN")

    # openai config
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")


settings = Settings()
