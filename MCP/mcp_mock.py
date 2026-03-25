# MCP Main Router (Weather + future Flight support)

from MCP.BMKG.weather_handler import weather_handler
from MCP.Flight.flight_handler import flight_handler

# Future:
# from MCP.Flight.flight_handler import flight_handler


def run_mcp(query: str, intent: str = None, force_context: bool = False, session: dict = None) -> dict:
    """
    Main MCP Router
    Routes to WEATHER or FLIGHT handler.
    """
    # weather
    if intent == "WEATHER":
        return weather_handler(query = query, force_context= force_context)
                # {
                # "status": "CORRECT",
                # "data": weather_handler(query=query, force_context=force_context)
                # }

    # flight
    if intent == "FLIGHT":
        # return flight_handler(query=query, force_context=force_context)
        return flight_handler(query= query, session= session)

    # fallback
    return {"status": "NO_MCP_MATCH"}