from app.core.settings import settings
from evals.judges.base_judge import BaseJudge
from evals.judges.gemini import GeminiJudge
from evals.judges.deepseek import DeepSeekJudge

class JudgeFactory:
    @staticmethod
    def create_judge(judge_type: str) -> BaseJudge:
        judge_type = judge_type.lower()
        
        if judge_type == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is missing from configuration!")
            return GeminiJudge(api_key=settings.GEMINI_API_KEY)
            
        elif judge_type == "deepseek":
            if not settings.DEEPSEEK_API_KEY:
                raise ValueError("DEEPSEEK_API_KEY is missing from configuration!")
            return DeepSeekJudge(api_key=settings.DEEPSEEK_API_KEY)
            
        else:
            raise ValueError(f"Unknown judge type requested: {judge_type}")
