from openai import AsyncOpenAI
from langfuse import observe
from app.infrastructure.llm.base import LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str, model_id: str):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model_id = model_id

    @observe(name="openai-generation", as_type="generation")
    async def generate(self, messages) -> str:
        response = await self.client.chat.completions.create(
            model=self.model_id,
            messages=messages
        )
        return response.choices[0].message.content
