import asyncio
import requests
from langfuse import observe
from app.infrastructure.llm.base import LLMProvider


class LMStudioProvider(LLMProvider):
    def __init__(self, model_id: str, base_url: str, temperature: float = 0):
        self.model_id = model_id
        self.base_url = base_url
        self.temperature = temperature

    @observe(name="lmstudio-generation", as_type="generation")
    async def generate(self, prompt: str) -> str:
        return await asyncio.to_thread(self._generate_sync, prompt)

    def _generate_sync(self, prompt: str) -> str:
        payload = {
            "model": self.model_id,
            "input": prompt,
            "temperature": self.temperature
        }

        try:
            r = requests.post(self.base_url, json=payload, timeout=200)
            r.raise_for_status()
            data = r.json()

            for item in data.get("output", []):
                if item.get("type") == "message":
                    return item.get("content", "").strip()
            return None

        except Exception as e:
            print("Local LLM Error (LM Studio):", e)
            return None
