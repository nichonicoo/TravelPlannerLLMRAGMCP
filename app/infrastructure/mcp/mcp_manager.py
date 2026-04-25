from typing import Dict, Callable
from app.infrastructure.mcp.BMKG.weather_handler import weather_handler
from app.infrastructure.mcp.Flight.flight_handler import flight_handler
from app.infrastructure.mcp.Hotel.hotel_handler import hotel_handler


class MCPManager:
    def __init__(self):
        # Register handlers in a dictionary mapping
        self._handlers: Dict[str, Callable] = {
            "WEATHER": self._handle_weather,
            "FLIGHT": self._handle_flight,
            "HOTEL": self._handle_hotel,
        }

    def execute(self, intent: str, query: str, session: dict = None, force_context: bool = False) -> dict:
        """Main entry point to run an MCP tool based on intent."""
        handler = self._handlers.get(intent.upper())

        if not handler:
            return {"status": "ERROR", "message": f"No handler found for intent: {intent}"}

        # Standardize the call to the actual handler functions
        return handler(query, session, force_context)

    # Private wrappers to normalize different handler signatures
    def _handle_weather(self, query, session, force):
        return weather_handler(query=query, force_context=force)

    def _handle_flight(self, query, session, force):
        return flight_handler(query=query, session=session)

    def _handle_hotel(self, query, session, force):
        return hotel_handler(query=query, session_data=session)
