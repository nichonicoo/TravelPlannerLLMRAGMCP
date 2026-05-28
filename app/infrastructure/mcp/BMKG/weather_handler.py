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
        Standardized Weather MCP response.

        Returns:
        - OK
        - AMBIGUOUS
        - NOT_FOUND
        - ERROR
        """
        query = params.get("query", "")
        explicit_location = params.get("location")

        if explicit_location:
            loc = self.resolver.getLocation(explicit_location, force=True)
        else:
            loc = self.resolver.getLocation(query)

        if loc["status"] == "NOT_FOUND":
            return {
                "status": "NOT_FOUND",
                "error": "Location not found in BMKG database"
            }

        if loc["status"] == "AMBIGUOUS":
            return {
                "status": "AMBIGUOUS",
                "data": {
                    "field": "location",
                    "candidates": loc.get("candidates", []),
                    "params": params
                }
            }

        data = self.client.get_bmkg_weather(loc["adm4"])

        if "error" in data:
            return {
                "status": "ERROR",
                "error": "BMKG API error",
                "data": {
                    "adm4": loc["adm4"],
                    "location_name": loc["location_name"],
                    "params": params
                }
            }

        return {
            "status": "OK",
            "data": {
                "location_name": loc["location_name"],
                "adm4": loc["adm4"],
                "weather": data,
                "params": params
            }
        }
