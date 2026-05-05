

from app.schemas.actions import ActionType


class ResponseFormatter:
    def format(self, intent: str, result: dict) -> str:
        action = result.get("action")

        if action == ActionType.ASK_CLARIFICATION:
            return result["message"]

        if action == ActionType.NEED_MORE_INFO:
            return result["message"]

        if action == ActionType.INVALID_INPUT:
            return result["message"]

        if action == ActionType.ERROR:
            return result["message"]

        if action == ActionType.GENERATE_RESPONSE:
            return self._format_by_intent(intent, result)

        return "Terjadi kesalahan."

    def _format_by_intent(self, intent: str, result: dict) -> str:
        if intent == "FLIGHT":
            return self._format_flight(result["message"])

        if intent == "WEATHER":
            return self._format_weather(result["message"])

        if intent == "HOTEL":
            return self._format_hotel(result["message"])

        if intent == "RAG":
            return self._format_rag(result["message"])

        if intent == "LLM":
            return result.get("message", "")

        return str(result)

    def _format_flight(self, message: str) -> str:
        return message

    def _format_weather(self, message: str) -> str:
        return message

    def _format_hotel(self, message: str) -> str:
        return message

    def _format_rag(self, data: dict) -> str:
        return str(data)
