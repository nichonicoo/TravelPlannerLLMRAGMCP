"""
Weather Handler
Responsible for:
- resolving location
- handling ambiguous cases
- calling BMKG API
- returning structured MCP response
"""

from app.infrastructure.mcp.BMKG.location_resolver import WeatherLocationResolver
from app.infrastructure.mcp.BMKG.mcp_bmkg import BMKGClient
import app.core.sessions as session


class WeatherHandler:
    def __init__(self, resolver=None, client=None):
        self.resolver = resolver or WeatherLocationResolver()
        self.client = client or BMKGClient()

    async def __call__(self, params: dict) -> dict:
        """
        Making the class 'callable' allows you to use it in 
        your MCPManager dict just like a function.
        """
        query = params.get("query", "")

        # 1. Technical logic
        loc = self.resolver.getLocation(query)

        if loc["status"] == "NOT_FOUND":
            return {"status": "ERROR", "message": "Lokasi tidak terdaftar di BMKG."}

        if loc["status"] == "AMBIGUOUS":
            return {
                "status": "AMBIGUOUS",
                "candidates": loc["candidates"],
                "message": "Pilih lokasi yang lebih spesifik:"
            }

        session.update_city(loc["location_name"], loc["adm4"])

        # 2. API logic
        data = self.client.get_bmkg_weather(loc["adm4"])

        if "error" in data:
            return {
                "status": "ERROR",
                "adm4": loc["adm4"],
                "location_name": loc["location_name"],
            }

        return {
            "status": "OK",
            "adm4": loc["adm4"],
            "location_name": loc["location_name"],
            "data": data
        }
