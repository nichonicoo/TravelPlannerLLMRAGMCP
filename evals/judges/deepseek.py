import json
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from evals.utils_scoring import EvaluationResponse, extract_json
from evals.judges.base_judge import BaseJudge


class DeepSeekJudge(BaseJudge):
    MODEL_NAME = "deepseek-v4-flash"

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def _call_model(self, system_prompt: str, user_prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=0.0,
            response_format={
                "type": "json_object",
                "schema": EvaluationResponse.model_json_schema()
            }
        )
        return response.choices[0].message.content

    async def evaluate(self, system_prompt: str, user_prompt: str) -> dict:
        raw_response = await self._call_model(system_prompt, user_prompt)
        cleaned = extract_json(raw_response)
        parsed = json.loads(cleaned)
        print(json.dumps(parsed, indent=2, ensure_ascii=False))

        validated = EvaluationResponse.model_validate(parsed)
        return validated.model_dump()
