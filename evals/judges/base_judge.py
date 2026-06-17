from abc import ABC, abstractmethod

class BaseJudge(ABC):
    @abstractmethod
    async def evaluate(self, system_prompt: str, user_prompt: str) -> dict:
        pass
