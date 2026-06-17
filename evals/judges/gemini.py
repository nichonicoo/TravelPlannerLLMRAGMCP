import json
from google import genai
from google.genai import types
from google.genai.errors import APIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from evals.utils_scoring import EvaluationResponse, extract_json
from evals.judges.base_judge import BaseJudge

class GeminiJudge(BaseJudge):
    MODEL_NAME = "gemma-4-31b-it"

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type(APIError),
        reraise=True,
    )
    async def _call_model(self, system_prompt: str, user_prompt: str):
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=EvaluationResponse,
            temperature=0.0,
        )

        return await self.client.aio.models.generate_content(
            model=self.MODEL_NAME,
            contents=user_prompt,
            config=config,
        )

    async def evaluate(self, system_prompt: str, user_prompt: str) -> dict:
        response = await self._call_model(system_prompt, user_prompt)
        raw_response = response.text
        cleaned = extract_json(raw_response)
        return json.loads(cleaned)
