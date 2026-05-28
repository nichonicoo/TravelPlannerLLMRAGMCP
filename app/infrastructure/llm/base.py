from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.schemas.message import Message

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: List[Message], **kwargs) -> Dict[str, Any]:
        """All providers return a dictionary with at least a 'response' key."""
        pass
