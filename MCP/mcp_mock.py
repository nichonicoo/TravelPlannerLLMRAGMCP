# from MCP.mcp_weather import get_weather
from MCP.BMKG.mcp_bmkg import get_bmkg_weather
# from MCP.BMKG.location_resolver import get_adm4_candidates
from MCP.BMKG.location_resolver import getLocation

# def run_mcp(query: str, intent: str = None, force_location: bool = False):
#     q = query.lower()

#     # 🔥 PRIORITY: intent dari router
#     if intent == "WEATHER":
#         result = get_adm4_candidates(query)

#         if result["status"] == "FOUND":
#             return get_bmkg_weather(result["adm4"])

#         if result["status"] == "AMBIGUOUS":
#             return {
#                 "status": "NEED_CONFIRMATION",
#                 "candidates": result["candidates"]
#             }

#         return {"status": "NOT_FOUND"}

#     # ---------------- fallback keyword-based ----------------
#     if "cuaca" in q:
#         result = get_adm4_candidates(query)

#         if result["status"] == "FOUND":
#             return get_bmkg_weather(result["adm4"])

#         if result["status"] == "AMBIGUOUS":
#             return {
#                 "status": "NEED_CONFIRMATION",
#                 "candidates": result["candidates"]
#             }

#         return {"status": "NOT_FOUND"}

#     return {"status": "NO_MCP"}

def run_mcp(query: str, intent: str = None, force_location: bool = False):
    
    if intent != "WEATHER":
        return {'status': "NOT_FOUND"}
    
    if force_location:
        # langsung anggap query adalah ADM4 valid
        adm4_code = getLocation(query)
        
        if adm4_code.get("status") == "FOUND":
            weather = get_bmkg_weather(adm4_code["adm4"])
            return {"status": "FOUND", "data": weather}
        
        return get_bmkg_weather(adm4_code["adm4"])

    result = getLocation(query)
    
    if result["status"] == "FOUND":
        weather = get_bmkg_weather(result["adm4"])
        return {"status": "FOUND", "data": weather}

    if result["status"] == "AMBIGUOUS":
        return {
            "status": "NEED_CONFIRMATION",
            "candidates": result["candidates"]
        }

    print('isi result ', result)
    return {'status': "NOT_FOUND"}