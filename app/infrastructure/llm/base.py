from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Standard method for all providers."""
        pass
