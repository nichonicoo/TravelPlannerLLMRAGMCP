from RAG.research_agent import run_research_agent
from MCP.mcp_mock import run_mcp
from utils.decision_routing import decision_routing
from utils.reference_detector import reference_prev_locations
from utils.llm_mode import LLM_answering
from utils.mcp_router import mcp_router
from MCP.BMKG.location_resolver import getLocation

# GLOBAL STATE (generic, not weather-specific)
PENDING_MCP = {
    "awaiting_confirmation": False,
    "intent": None,
    "last_location_name": None, # ex: "Yogya"
    "last_adm4": None
}


def langchain_router(query, retriever, gemini):
    
    # reference to prev locations 
    if PENDING_MCP["last_adm4"] and reference_prev_locations(query= query):
        print('use previous location')
        api_data = run_mcp(
            query= PENDING_MCP["last_location_name"],
            intent= "WEATHER"
        )
        
        if api_data.get("status") == "OK":
            return api_data.get("data")
        
        return api_data

    # ================= CONTEXT MODE =================
    if PENDING_MCP["awaiting_confirmation"]:
        print("🧠 MCP CONTEXT MODE")

        api_data = run_mcp(
            query=query,
            intent=PENDING_MCP["intent"],
            # force_context=True
        )

        status = api_data.get("status")

        # Still ambiguous
        if status in ["AMBIGUOUS", "NEED_CONFIRMATION"]:
            candidates = ", ".join(api_data.get("candidates", []))
            return f"""
                    Data belum lengkap.

                    Apakah yang Anda maksud:
                    - {candidates}

                    Silakan pilih salah satu.
                    """

        # Found → reset state
        if status == "OK":
            PENDING_MCP["awaiting_confirmation"] = False
            PENDING_MCP["intent"] = None
            PENDING_MCP["last_location_name"] = api_data.get("location_name")
            PENDING_MCP["last_adm4"] = api_data.get("adm4")
            
            return api_data.get("data")

        # Fallback
        return api_data

    # ================= NORMAL ROUTING =================
    route = decision_routing(query)
    print(f"🔀 ROUTER DECISION: {route}")

    # ---------------- RAG ----------------
    # if route == "RAG":
    #     print("🟦 ROUTER: RAG")
    #     rag_answer = run_research_agent(query, retriever, gemini)

    #     if "Informasi tidak tersedia" in rag_answer:
    #         return gemini.generate_content(query).text

    #     return rag_answer

    # ---------------- MCP ----------------
    if route == "MCP":
        print("🟩 ROUTER: MCP")
        
        intent = mcp_router(query=query)

        # If MCP intent cannot be determined
        if not intent:
            return {"status": "NO_MCP_MATCH"}

        api_data = run_mcp(query=query, intent=intent)
        status = api_data.get("status")
        
        if PENDING_MCP["last_location_name"] and reference_prev_locations(query):
            print("🔁 Passing last location to MCP")
            api_data = run_mcp(
                query=PENDING_MCP["last_location_name"],
                intent=intent
            )
        else:
            api_data = run_mcp(
                query=query,
                intent=intent
            )

        # Ambiguous → activate context mode
        if status in ["AMBIGUOUS", "NEED_CONFIRMATION"]:
            PENDING_MCP["awaiting_confirmation"] = True
            PENDING_MCP["intent"] = intent

            candidates = ", ".join(api_data.get("candidates", []))
            return f"""
                    Data belum lengkap.

                    Apakah yang Anda maksud:
                    - {candidates}

                    Silakan pilih salah satu.
                    """
        
        if status == "OK":
            PENDING_MCP["last_location_name"] = api_data.get("location_name")
            PENDING_MCP["last_adm4"] = api_data.get("adm4")

            return api_data.get("data")

        return api_data["data"]

    # ---------------- DIRECT LLM ----------------
    print("🟨 ROUTER: Direct LLM")
    
    LLM_answer = LLM_answering(query=query)
    
    locations = getLocation(query = query)
    
    if locations.get("status") == "FOUND":
        PENDING_MCP["last_location_name"] = locations.get("location_name")
        PENDING_MCP["last_adm4"] = locations.get("adm4")
        print("📌 Saved location context:", PENDING_MCP["last_location_name"])
    
    
    # possible_location = extra
    
    return LLM_answer