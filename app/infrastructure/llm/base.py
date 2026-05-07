from abc import ABC, abstractmethod
from typing import List
from app.schemas.message import Message


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: List[Message]) -> str:
        """Standard method for all providers."""
        pass
