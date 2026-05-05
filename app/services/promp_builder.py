from typing import Dict, List, Any
from app.schemas.message import Message


class PromptBuilder:
    def __init__(self):
        self._builders = {
            "FLIGHT": self._build_flight_prompt,
            "WEATHER": self._build_weather_prompt,
            "HOTEL": self._build_hotel_prompt,
            "RAG": self._build_rag_prompt,
            "LLM": self._build_generic_prompt,
        }

    def build(self, intent: str, context: Dict[str, Any]) -> List[Message]:
        builder = self._builders.get(intent, self._build_fallback_prompt)
        return builder(context)

    def _safe_user_query(self, context: Dict[str, Any]) -> str:
        return context.get("query", "").strip()

    # ------------------------
    # Intent-specific builders
    # ------------------------

    def _build_flight_prompt(self, context: Dict[str, Any]) -> List[Message]:
        data = context.get("data", "unknown data")

        return [
            {
                "role": "system",
                "content": "You are a flight booking assistant. Provide clear options and relevant details."
            },
            {
                "role": "user",
                "content": f"{self._safe_user_query(context)} (Data: {data})"
            }
        ]

    def _build_weather_prompt(self, context: Dict[str, Any]) -> List[Message]:
        data = context.get("data", "unknown location")

        return [
            {
                "role": "system",
                "content": "You are a weather assistant. Provide concise and accurate weather information."
            },
            {
                "role": "user",
                "content": f"{self._safe_user_query(context)} (Data: {data})"
            }
        ]

    def _build_hotel_prompt(self, context: Dict[str, Any]) -> List[Message]:
        data = context.get("data", "unknown data")

        return [
            {
                "role": "system",
                "content": "You are a hotel recommendation assistant. Suggest relevant options based on user needs."
            },
            {
                "role": "user",
                "content": f"{self._safe_user_query(context)} (Data: {data})"
            }
        ]

    def _build_rag_prompt(self, context: Dict[str, Any]) -> List[Message]:
        documents = context.get("data", [])

        docs_text = "\n\n".join(
            documents) if documents else "No documents provided."

        return [
            {
                "role": "system",
                "content": "Answer the question using ONLY the provided context. If unsure, say you don't know."
            },
            {
                "role": "system",
                "content": f"Context:\n{docs_text}"
            },
            {
                "role": "user",
                "content": self._safe_user_query(context)
            }
        ]

    def _build_generic_prompt(self, context: Dict[str, Any]) -> List[Message]:
        return [
            {
                "role": "system",
                "content": (
                    "Kamu adalah Travel Agent di Indonesia.\n"
                    "Jawab dalam Bahasa Indonesia, singkat (1-3 kalimat), jelas, dan langsung ke poin.\n"
                    "\n"
                    "Aturan:\n"
                    "- Hanya berikan jawaban, tanpa pilihan A/B/C/D.\n"
                    "- Jangan mengulang jawaban.\n"
                    "- Jangan mengarang.\n"
                    "- Jika pertanyaan tidak jelas, minta klarifikasi.\n"
                )
            },
            {"role": "user", "content": self._safe_user_query(context)}
        ]

    def _build_fallback_prompt(self, context: Dict[str, Any]) -> List[Message]:
        return [
            {
                "role": "system",
                "content": "You are a general assistant. Handle the request appropriately."
            },
            {
                "role": "user",
                "content": self._safe_user_query(context)
            }
        ]
