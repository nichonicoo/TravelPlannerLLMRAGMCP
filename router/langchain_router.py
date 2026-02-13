from RAG.research_agent import run_research_agent
from MCP.mcp_mock import run_mcp
from utils.reference_detector import reference_prev_locations
from utils.return_text_bmkg import return_weather_beautifier
from utils.decision_routing import decision_routing
from utils.llm_mode import LLM_answering

# GLOBAL STATE (lightweight session state)
PENDING_MCP = {
    "awaiting_location": False, 
    "last_intent": None,  # ex: "WEATHER"
    "last_location_name": None, # ex: "Yogya"
    "last_adm4": None
}

# CHEAP ROUTER (RULE-BASED, HEMAT QUOTA)
# def cheap_route(query: str) -> str:
#     q = query.lower()

#     if any(k in q for k in ["cuaca", "hujan", "panas", "dingin"]):
#         return "MCP"

#     if any(k in q for k in ["prospektus", "saham", "laporan", "risiko"]):
#         return "RAG"

#     return "LLM"


# ROUTER UTAMA (STATE-AWARE)
def langchain_router(query, retriever, gemini):
    
    if PENDING_MCP["last_location_name"]:
        if reference_prev_locations(query):
            print("🧠 Contextual reference detected → reuse last location")
            
            api_data = run_mcp(
                PENDING_MCP["last_location_name"],
                intent="WEATHER",
                force_location=True  # opsional, tergantung implementasi kamu
            )
            
            if api_data.get("status") == "OK":
                return return_weather_beautifier(api_data.get("source", "BMKG"))

    # 🔒 FORCE MCP JIKA LAGI NUNGGU KONFIRMASI LOKASI
    if PENDING_MCP["awaiting_location"]:
        print("🧠 CONTEXT: awaiting location confirmation → force MCP")
        
        routing_to = decision_routing(query= query)
        
        if routing_to != ["MCP", "RAG"]:
            print('Routing to LLM not to MCP n RAG')
            PENDING_MCP["awaiting_location"] = False
        else: 
            api_data = run_mcp(query, 
                               intent=PENDING_MCP["last_intent"], 
                               force_location= True
                               )
            print('result api_data: ', api_data)    
            
            # Masih ambigu → tanya lagi
            if api_data.get("status") in ["AMBIGUOUS", "NEED_CONFIRMATION"]:
                candidates = ", ".join(api_data.get("candidates", []))
                return f"""
                        Lokasi masih belum dikenali secara pasti.

                        Apakah yang Anda maksud:
                        - {candidates}

                        Silakan ketik salah satu nama lokasi di atas.
                        """
                    
            # Sudah ketemu → reset state & lanjut MCP
            if api_data.get("status") == "FOUND":
                PENDING_MCP["awaiting_location"] = False
                PENDING_MCP["last_intent"] = None
                PENDING_MCP["last_location_name"] = api_data.get("location_name")
                PENDING_MCP["last_adm4"] = api_data.get("adm4")

                return return_weather_beautifier(api_data.get("source", "BMKG"))
        
    # return "Maaf, lokasi masih belum dikenali. Silakan sebutkan nama kota yang lebih jelas."
    

    # ROUTING NORMAL (RULE-BASED)
    # route = cheap_route(query)
    route = decision_routing(query)
    print(f"🔀 ROUTER DECISION: {route}")

    # ---------------- RAG ----------------
    if route == "RAG":
        print("🟦 ROUTER: Research Agent (RAG) dipakai")

        rag_answer = run_research_agent(query, retriever, gemini)

        if "Informasi tidak tersedia" in rag_answer:
            return gemini.generate_content(query).text

        return rag_answer

    # ---------------- MCP ----------------
    if route == "MCP":
        print("🟩 ROUTER: MCP dipakai")

        api_data = run_mcp(query, intent="WEATHER")
        
        print('result api_data if routing in MCP', api_data)

        if api_data.get("status") in ["AMBIGUOUS", "NEED_CONFIRMATION"]:
            PENDING_MCP["awaiting_location"] = True
            PENDING_MCP["last_intent"] = "WEATHER"

            candidates = ", ".join(api_data.get("candidates", []))
            return f"""
                    Lokasi tidak dikenali secara pasti.

                    Apakah yang Anda maksud:
                    - {candidates}

                    Silakan ketik salah satu nama lokasi di atas.
                    """

        if api_data.get("status") == "NOT_FOUND":
            return "Maaf, lokasi tidak dikenali. Silakan sebutkan nama kota yang lebih jelas."

        return return_weather_beautifier(api_data)

    # ---------------- DIRECT LLM ----------------
    print("🟨 ROUTER: Small LLM Local Qwen")
    return LLM_answering(query= query)