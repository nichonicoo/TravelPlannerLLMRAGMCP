from typing import Dict, Callable
from app.infrastructure.mcp.BMKG.weather_handler import WeatherHandler
from app.infrastructure.mcp.Flight.flight_handler import FlightHandler
from app.infrastructure.mcp.Hotel.hotel_handler import HotelHandler


class MCPManager:
    def __init__(self):
        # Register handlers in a dictionary mapping
        self._handlers: Dict[str, Callable] = {
            "WEATHER": WeatherHandler(),
            "FLIGHT": FlightHandler(),
            "HOTEL": HotelHandler(),
        }

    async def execute(self, intent: str, params: dict) -> dict:
        """Main entry point to run an MCP tool based on intent."""
        handler = self._handlers.get(intent)

        if not handler:
            return {"status": "ERROR", "message": f"No handler found for intent: {intent}"}

        # All handlers now have standardized signature: handler(params: dict) -> dict
        return await handler(params)
