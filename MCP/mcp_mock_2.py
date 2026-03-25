from MCP.BMKG.mcp_bmkg import get_bmkg_weather
from MCP.BMKG.location_resolver import getLocation

# #
# def run_mcp(query: str, intent: str = None, force_location: bool = False):
    
#     if intent != "WEATHER":
#         return {'status': "NOT_FOUND"}
    
#     if force_location:
#         # langsung anggap query adalah ADM4 valid
#         adm4_code = getLocation(query)
        
#         if adm4_code.get("status") == "FOUND":
#             weather = get_bmkg_weather(adm4_code["adm4"])
#             return {"status": "FOUND", "data": weather}
        
#         return get_bmkg_weather(adm4_code["adm4"])

#     result = getLocation(query)
    
#     if result["status"] == "FOUND":
#         weather = get_bmkg_weather(result["adm4"])
#         return {"status": "FOUND", "data": weather}

#     if result["status"] == "AMBIGUOUS":
#         return {
#             "status": "NEED_CONFIRMATION",
#             "candidates": result["candidates"]
#         }

#     print('isi result ', result)
#     return {'status': "NOT_FOUND"}

# MCP Router (Weather + future Flight support)

from MCP.BMKG.mcp_bmkg import get_bmkg_weather
from MCP.BMKG.location_resolver import getLocation

# Future:
# from MCP.Flight.flight_handler import handle_flight


def run_mcp(query: str, intent: str = None, force_location: bool = False):
    """
    Main MCP Router
    Routes to WEATHER or FLIGHT handler.
    """

    # ================= WEATHER =================
    if intent == "WEATHER":

        if force_location:
            adm4_code = getLocation(query)

            if adm4_code.get("status") == "FOUND":
                weather = get_bmkg_weather(adm4_code["adm4"])
                return {"status": "FOUND", "data": weather}

            return {"status": "NOT_FOUND"}

        result = getLocation(query)

        if result["status"] == "FOUND":
            weather = get_bmkg_weather(result["adm4"])
            return {"status": "FOUND", "data": weather}

        if result["status"] == "AMBIGUOUS":
            return {
                "status": "NEED_CONFIRMATION",
                "candidates": result["candidates"]
            }

        return {"status": "NOT_FOUND"}

    # ================= FLIGHT (placeholder) =================
    if intent == "FLIGHT":
        # return handle_flight(query)
        return {"status": "FLIGHT_HANDLER_NOT_IMPLEMENTED"}

    # ================= FALLBACK =================
    return {"status": "NO_MCP_MATCH"}