import router.sessions as session
from LLM.orchestrator import decision_routing, reference_prev_locations, city_to_iata
from LLM.llm_mode import llm_answering
from MCP.mcp_mock import run_mcp
from LLM.orchestrator import city_to_iata
try: 
    from RAG.research_agent import run_research_agent
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    
def handle_weather_result(result: dict) -> str: 
    status = result.get("status")
    
    if status == "OK":
        session.update_city(
            cityname=result.get("location_name", session.get()["last_city_name"]),
            adm4=result.get("adm4"),
        )
        session.clear_confirmation()
        return result["data"]
    
    if status == "AMBIGUOUS":
        session.set_confirmation("WEATHER", result.get("candidates", []))
        candidates_str = "\n- ".join(session.get()["candidates"])
        return f"Lokasi tidak dikenali secara pasti. Maksudnya yang mana?\n- {candidates_str}"
    
    if status == "NOT_FOUND":
        return "Maaf, lokasi tidak dikenali. Sebutkan nama kota yang lebih spesifik."
 
    return "Maaf, terjadi kesalahan saat mengambil data cuaca."

def handle_flight_result(result: dict) -> str:
    status = result.get("status")
    
    if status == "OK":
        session.update_flight(result.get("params", {}))
        session.clear_confirmation()
        return result["data"]
 
    if status == "NEED_INFO":
        session.set_confirmation("FLIGHT", [])
        return result["message"]
    
    if status == "NOT_FOUND":
        return "Tidak ada penerbangan tersedia untuk rute dan tanggal tersebut."
 
    return f"Terjadi kesalahan: {result.get('message', 'unknown error')}"

def langchain_router(query: str, retriever = None, gemini = None) -> str: 
    s = session.get()
    
    session.tick()
    print(f"[Session] {session.summary()}")
    
    # confirmation mode -> waiting confirmation from user
    if s["awaiting_confirmation"]:
        intent = s["pending_intent"]
        print(f"[Router] Confirmation mode → intent: {intent}")
        
        if intent == "WEATHER":
            result = run_mcp(query=query, intent="WEATHER", force_context=True)
            return handle_weather_result(result)
        
        if intent == "FLIGHT":
            # User lagi jawab pertanyaan clarifikasi (misal: "dari jakarta")
            # Merge jawaban user ke params yang sudah ada
            old_params = s.get("last_flight_params") or {}
            result = run_mcp(
                query=query,
                intent="FLIGHT",
                session=s,
            )
            return handle_flight_result(result)

    # 2 classified the intent
    action = decision_routing(query)
    print(f"[Router] Action: {action}")
    
    # reset if topik bkn non travel
    session.smart_reset_if_needed(action, query)
    
    # 3. cek kata2 referensi kaya :dimana disitu kesana 
    
    if reference_prev_locations(query) and session.has_city():
        session.touch_city()
        print(f"[Router] Konteks dirujuk → pakai kota: {s['last_city_name']}")
        
        if action == "WEATHER":
            result = run_mcp(
                query=s["last_city_name"],
                intent="WEATHER",
                force_context=True,
            )
            return handle_weather_result(result)
        
        if action == "FLIGHT":
            origin = s["last_origin"]
            if not origin:
                session.set_confirmation("FLIGHT", [])
                return f"Mau terbang ke {s['last_city_name']} dari kota mana?"
 
            result = run_mcp(
                query=f"tiket dari {origin} ke {s['last_city_name']}",
                intent="FLIGHT",
                session=s,
            )
            return handle_flight_result(result)
        
        
    # 4. normal routing
    
    if action == "WEATHER":
        result = run_mcp(query=query, intent="WEATHER")
        return handle_weather_result(result)
    
    if action == "FLIGHT":
        origin = s["last_origin"]
        if not origin:
            # Cek dulu apakah query sudah menyebut origin
            # flight_params_extractor akan handle ini di dalam flight_handler
            result = run_mcp(query=query, intent="FLIGHT", session=s)
            # Kalau NEED_INFO berarti origin belum ada
            if result.get("status") == "NEED_INFO" and "origin" in result.get("missing", []):
                session.set_confirmation("FLIGHT", [])
            return handle_flight_result(result)
 
        result = run_mcp(query=query, intent="FLIGHT", session=s)
        return handle_flight_result(result)
    
    # RAG
    if action == "RAG":
        if not RAG_AVAILABLE or retriever is None:
            return "Maaf, fitur dokumen belum dimuat. Coba tanya hal lain dulu."
        rag_answer = run_research_agent(query, retriever, gemini)
        if "Informasi tidak tersedia" in rag_answer:
            return llm_answering(query)
        return rag_answer
 
    # LLM — jawab langsung, tapi tetap ekstrak kota kalau ada
    answer = llm_answering(query)
    
    # Simpan kota ke session kalau ada di query
    from LLM.orchestrator import extract_city
    city = extract_city(query)
    if city:
        iata = city_to_iata(city)
        session.update_city(cityname=city, iata=iata)
        print(f"[Session] Kota diekstrak dari LLM turn: {city} ({iata})")
 
    return answer
    