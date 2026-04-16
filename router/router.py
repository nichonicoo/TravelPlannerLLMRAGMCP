import router.sessions as session
from LLM.orchestrator import decision_routing, reference_prev_locations, city_to_iata
from LLM.llm_mode import llm_answering
from MCP.mcp_mock import run_mcp
from LLM.orchestrator import city_to_iata, extract_city, get_airport_full_name
from RAG.rag_pipeline import init_vector_db, retrieve_context, build_prompt

vector_db = init_vector_db()
    
# was 1    
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
        
        # new
        session.get()["pending_query"] = result.get("original_query")
        candidates = result.get("candidates", [])
        candidates_str = "\n".join([f"{i+1}. {c}" for i, c in enumerate(candidates)]) 
        
        # candidates_str = "\n- ".join(session.get()["candidates"])
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
    
    if status == "AMBIGOUS":
        session.set_confirmation("FLIGHT", result.get("candidates", []))
        session.get()["pending_params"] = result.get("params")
        
        candidates = result.get("candidates", [])
        
        # candidates_str = "\n".join([f"{i+1}. {c}" for i, c in enumerate(candidates)])
        candidates_str = "\n".join([
            f"{i+1}. {get_airport_full_name(c)}"
            for i, c in enumerate(candidates)
        ])
    
        return f"Bandara tidak spesifik. Pilih salah satu:\n{candidates_str}"
        
        # new 
        # session.get()["pending_params"] = result.get("params")
        # candidates_str = "\n- ".join(session.get()["candidates"])
        
        # # candidates_str = "\n- ".join(session.get()["candidates"])
        # return f"Lokasi tidak dikenali secara pasti. Maksudnya yang mana?\n- {candidates_str}"
    
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
            # new 
            choice = query.strip()
            candidates = s["candidates"]
            
            selected = None
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(candidates):
                    selected = candidates[idx]
            else:
                selected = choice
            
            if not selected:
                return "Pilihan tidak valid. Pilih nomor atau tulis nama lokasi."
            
            result = run_mcp(query=selected, intent="WEATHER", force_context=True)
            
            return handle_weather_result(result)
        
        if intent == "FLIGHT":
            # User lagi jawab pertanyaan clarifikasi (misal: "dari jakarta")
            # Merge jawaban user ke params yang sudah ada
            candidates = s.get("candidates", [])
            choice = query.strip()

            selected = None
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(candidates):
                    selected = candidates[idx]
            else:
                selected = choice.upper()

            if not selected:
                return "Pilihan tidak valid."
            
            # ambil param lama
            params = s.get("pending_params") or {}

            # tentukan dia isi origin atau destination
            if isinstance(params.get("departure_id"), list):
                params["departure_id"] = selected
            elif isinstance(params.get("arrival_id"), list):
                params["arrival_id"] = selected

            # langsung call search tanpa re-extract
            from MCP.Flight.flight_search import search_flight_offers
            from MCP.Flight.flight_beautifier import beautify_flight_offerst

            result = search_flight_offers(
                origin=params.get("departure_id"),
                destination=params.get("arrival_id"),
                type=params.get("type"),
                departure_date=params.get("outbound_date"),
                return_date=params.get("return_date"),
                adults=params.get("adults", 1),
                travel_class=params.get("travel_class"),
                currency=params.get("currency")
            )

            if result["status"] != "OK":
                return "Gagal mencari tiket."

            session.clear_confirmation()

            return beautify_flight_offerst(result)

            # old_params = s.get("last_flight_params") or {}
            # merged_query = f"{old_params} {query}"
            
            # result = run_mcp(
            #     query=query,
            #     intent="FLIGHT",
            #     session=s,
            # )
            # return handle_flight_result(result)
            
        

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
        print('weather now')
        result = run_mcp(query=query, intent="WEATHER")
        return handle_weather_result(result)
    
    if action == "FLIGHT":
        print('flight now')
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
    
    if action == "HOTEL":
        print('hotel now')
        result = run_mcp(query=query, intent="HOTEL", session=s)

        if result.get("status") == "NEED_INFO":
            return result.get("message")

        if result.get("status") == "ERROR":
            return result.get("message")

        return result.get("data")
    
    # RAG
    if action == "RAG":
        print("[Router] RAG mode")

        context = retrieve_context(vector_db, query)

        if not context.strip():
            return llm_answering(query)

        prompt = build_prompt(context, query)
        answer = llm_answering(prompt)

        if "tidak tahu" in answer.lower():
            return llm_answering(query)

        return answer
 
    # LLM — jawab langsung, tapi tetap ekstrak kota kalau ada
    answer = llm_answering(query)
    
    # Simpan kota ke session kalau ada di query
    from LLM.orchestrator import extract_city
    print('extract city now')
    city = extract_city(query)
    print('city extracted: ', city)
    if city:
        iata = city_to_iata(city)
        print('city to iata extracted: ', city)
        session.update_city(cityname=city, iata=iata)
        print(f"[Session] Kota diekstrak dari LLM turn: {city} ({iata})")
 
    return answer
    