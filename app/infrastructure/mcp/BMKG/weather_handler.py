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

resolver = WeatherLocationResolver()
client = BMKGClient()


def weather_handler(query: str, force_context: bool = False):
    """
    Main orchestration layer for WEATHER MCP
    """

    # ---------------- REFERENCE REUSE ----------------
    # from LLM.orchestrator import reference_prev_locations
    # if reference_prev_locations(query) and WEATHER_STATE["last_adm4"]:
    #     weather_data = get_bmkg_weather(WEATHER_STATE["last_adm4"])

    #     return return_weather_beautifier(weather_data)

    # Step 1: Resolve location
    resolution = resolver.getLocation(query, force=force_context)
    status = resolution.get("status")

    # ---------------- AMBIGUOUS ----------------
    if status in ["AMBIGUOUS", "NEED_CONFIRMATION"]:
        return {
            "status": "AMBIGUOUS",
            "intent": "WEATHER",
            "candidates": resolution.get("candidates", []),
            "original_query": query
        }

    # ---------------- NOT FOUND ----------------
    if status == "NOT_FOUND":
        return {
            "status": "NOT_FOUND",
            "intent": "WEATHER"
        }

    # ---------------- FOUND ----------------
    if status == "FOUND":
        adm4 = resolution.get("adm4")
        location_name = resolution.get("location_name")

        # Save context
        # WEATHER_STATE["last_location_name"] = location_name
        # WEATHER_STATE["last_adm4"] = adm4

        weather_data = client.get_bmkg_weather(adm4)

        if not weather_data:
            return {
                "status": "ERROR",
                "intent": "WEATHER",
                "message": "Gagal mengambil data cuaca dari BMKG."
            }

        return {
            "status": "OK",
            "adm4": adm4,
            "location_name": location_name,
            "data": weather_data,
            "original_query": query
        }

    # ---------------- FALLBACK ----------------
    return {
        "status": "ERROR",
        "intent": "WEATHER",
        "message": "Terjadi kesalahan dalam pemrosesan cuaca."
    }
