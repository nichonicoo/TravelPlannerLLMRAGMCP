# from MCP.Flight.mcp_flight import search_flight_offers
from MCP.Flight.flight_param_extractor import extract_flight_param, missing_params
from MCP.Flight.flight_search import search_flight_offers
from MCP.Flight.flight_beautifier import beautify_flight_offerst
from LLM.orchestrator import extract_city, city_to_iata, reference_prev_locations
# yang lalu 1
# def flight_handler(query: str, session: dict = None, force_params: dict = None) -> dict: 
#     """
#     Main entry point flight MCP.
 
#     Args:
#         query       : query natural language dari user
#         session     : SESSION dict dari router (untuk konteks kota)
#         force_params: kalau user sudah jawab pertanyaan clarifikasi,
#                       params bisa di-pass langsung
 
#     Returns:
#         {
#             "status": "OK" | "NEED_INFO" | "NOT_FOUND" | "ERROR",
#             "data": str (beautified),        # kalau OK
#             "message": str,                  # kalau NEED_INFO / ERROR
#             "missing": [str],                # field apa yang kurang
#             "params": dict,                  # params yang sudah diekstrak
#             "raw_offers": list,              # untuk flight price check nanti
#         }
#     """
#     # extract the params
#     params = extract_flight_param(query, session)
#     print("params: ", params)
    
#     if not params: 
#         return {
#             "status": "NEED_INFO",
#             "message": "Maaf, saya tidak bisa memahami detail penerbangan yang dimaksud. "
#                        "Mohon sebutkan kota asal, tujuan, dan tanggal keberangkatan.",
#             "missing": ["origin", "destination", "departure_date"],
#             "params": {},
#         }
    
    
#     # check if there's mutiple origin or destination IATAS
    
#     print('extract city now - 3 ')
#     city = extract_city(query)
#     print('city extracted: ', city)
    
#     if city:
#         iata = city_to_iata(city)
#         origin_list = iata.get('origin_iatas', [])
#         destination_list = iata.get('destination_iatas', [])
        
#         if origin_list:
#             params["departure_id"] = origin_list if len(origin_list) > 1 else origin_list[0]

#         if destination_list:
#             params["arrival_id"] = destination_list if len(destination_list) > 1 else destination_list[0]
            
#         if isinstance(params["departure_id"], list) or isinstance(params["arrival_id"], list):

#             candidates = []

#             if isinstance(params["departure_id"], list):
#                 candidates = params["departure_id"]

#             elif isinstance(params["arrival_id"], list):
#                 candidates = params["arrival_id"]

#             print('city to iata extracted: ', candidates)

#             return {
#                 "status": "AMBIGOUS",
#                 "message": "Menemukan beberapa pilihan bandara. Pilih salah satu:",
#                 "candidates": candidates,
#                 "params": params,
#             }
        
#         # candidates = []
#         # if len(origin_list) > 1:
#         #     candidates = origin_list
#         # elif len(destination_list) > 1:
#         #     candidates = destination_list
            
#         # print('city to iata extracted: ', candidates)
#         # print(f"[Session] Kota diekstrak dari LLM turn: {city} ({iata})")
        
#         # return {
#         #     "status": "AMBIGOUS",
#         #     "message": "Menemukan beberapa pilihan bandara. Pilih salah satu:",
#         #     "candidates": candidates,   # 🔧 FIX
#         #     "params": params,           # tetap simpan params lama
#         # }
        

#         # if len(origin_list) > 1 or len(destination_list) > 1: 
#         #     return {
#         #     "status": "AMBIGOUS",
#         #     "message": "Menemukan beberapa IATA CODE lebih dari 1  "
#         #                "Mohon sebutkan yang lebih spesifik",
#         #     "missing": ["origin", "destination", "departure_date"],
#         #     "params": iata,
#         # } 
#         # print('city to iata extracted: ', candidates)
#         # print(f"[Session] Kota diekstrak dari LLM turn: {city} ({iata})")
    
#     # check if params is lengkap 
#     missing = missing_params(params)
    
#     if missing: 
#         missing_labels = {
#             "departure_id": "kota asal",
#             "arrival_id": "kota tujuan",
#             "outbound_date": "tanggal keberangkatan",
#         }
#         missing_str = ", ".join(missing_labels.get(m, m) for m in missing)
#         return {
#             "status": "NEED_INFO",
#             "message": f"Mohon lengkapi info berikut: {missing_str}.",
#             "missing": missing,
#             "params": params,
#         }
#     print(f"[Flight Handler] Params: {params}")
    
#     result = search_flight_offers(
#         origin=params.get("departure_id"),
#         destination=params.get("arrival_id"),
#         type = params.get("type"),
#         departure_date=params.get("outbound_date"),
#         return_date=params.get("return_date"),
#         adults=params.get("adults", 1),
#         children = params.get("children", None),
#         infants_in_seat = params.get("infants_in_seat", None),
#         infants_on_lap = params.get("infants_on_lap", None),
#         travel_class=params.get("travel_class", "ECONOMY"),
#         currency=params.get("currency")
#     )
#     print('results: ', result)
    
#     if result["status"] != "OK":
#         return {
#             "status": result["status"],
#             "message": result.get("message", "Terjadi kesalahan."),
#             "params": params,
#         }
    
#     beautify = beautify_flight_offerst(result= result)
    
#     return {
#         "status": "OK",
#         "data": beautify,
#         "params": params,
#         "raw_offers": result.get("raw", []),   # disimpan untuk price check nanti
#     }

# def flight_handler(query: str, session: dict = None) -> dict:
#     """
#     Clean Flight Handler

#     Flow:
#     1. Extract params (LLM, non-location)
#     2. Inject origin/destination from session
#     3. Validate
#     4. Handle ambiguity
#     5. Call API
#     6. Beautify
#     """

#     session = session or {}

#     # =========================
#     # 1. Extract NON-LOCATION params
#     # =========================
#     params = extract_flight_param(query, session)

#     if not params:
#         return {
#             "status": "NEED_INFO",
#             "message": "Mohon sebutkan tanggal keberangkatan.",
#             "params": {}
#         }

#     print("[Flight Handler] Params from LLM:", params)

#     # =========================
#     # 2. Inject LOCATION from SESSION
#     # =========================
#     if session.get("origin_iata"):
#         params["departure_id"] = session["origin_iata"]

#     if session.get("destination_iata"):
#         params["arrival_id"] = session["destination_iata"]

#     print("[Flight Handler] After session inject:", params)

#     # =========================
#     # 3. VALIDATION
#     # =========================
#     missing = []

#     if not params.get("departure_id"):
#         missing.append("departure_id")

#     if not params.get("arrival_id"):
#         missing.append("arrival_id")

#     if not params.get("outbound_date"):
#         missing.append("outbound_date")

#     if missing:
#         label_map = {
#             "departure_id": "kota asal",
#             "arrival_id": "kota tujuan",
#             "outbound_date": "tanggal keberangkatan"
#         }

#         return {
#             "status": "NEED_INFO",
#             "message": f"Mohon lengkapi: {', '.join(label_map[m] for m in missing)}",
#             "missing": missing,
#             "params": params
#         }

#     # =========================
#     # 4. AMBIGUITY HANDLING
#     # =========================
#     if isinstance(params.get("departure_id"), list):
#         return {
#             "status": "AMBIGUOUS",
#             "message": "Pilih bandara asal:",
#             "candidates": params["departure_id"],
#             "field": "departure_id",
#             "params": params
#         }

#     if isinstance(params.get("arrival_id"), list):
#         return {
#             "status": "AMBIGUOUS",
#             "message": "Pilih bandara tujuan:",
#             "candidates": params["arrival_id"],
#             "field": "arrival_id",
#             "params": params
#         }

#     print("[Flight Handler] Final Params:", params)

#     # =========================
#     # 5. CALL API
#     # =========================
#     result = search_flight_offers(
#         origin=params.get("departure_id"),
#         destination=params.get("arrival_id"),
#         type = params.get("type"),
#         departure_date=params.get("outbound_date"),
#         return_date=params.get("return_date"),
#         adults=params.get("adults", 1),
#         children = params.get("children", None),
#         infants_in_seat = params.get("infants_in_seat", None),
#         infants_on_lap = params.get("infants_on_lap", None),
#         travel_class=params.get("travel_class", "ECONOMY"),
#         currency=params.get("currency")
#     )

#     if result["status"] != "OK":
#         return {
#             "status": result["status"],
#             "message": result.get("message", "Terjadi kesalahan."),
#             "params": params
#         }

#     # =========================
#     # 6. BEAUTIFY
#     # =========================
#     beautified = beautify_flight_offerst(result=result)

#     return {
#         "status": "OK",
#         "data": beautified,
#         "params": params,
#         "raw_offers": result.get("raw", [])
#     }
    
DESTINATION_ALIASES = {
    "canggu": "bali",
    "ubud": "bali",
    "kuta": "bali",
    "seminyak": "bali",
    "malioboro": "yogyakarta",
    "borobudur": "yogyakarta",
}

def normalize_city_name(name: str):
    if not name:
        return None
    key = name.lower().strip()
    return DESTINATION_ALIASES.get(key, key)

    
def flight_handler(query: str, session: dict = None) -> dict:
    session = session or {}

    print("\n=== FLIGHT HANDLER START ===")

    # =========================
    # 🔥 STEP 0: PREPROCESS
    # =========================
    is_reference = reference_prev_locations(query)

    if not is_reference:
        city = extract_city(query)

        if city:
            origin = normalize_city_name(city.get("origin"))
            destination = normalize_city_name(city.get("destination"))

            iata = city_to_iata({
                "origin": origin,
                "destination": destination
            })

            if origin:
                session["origin_city"] = origin
                session["origin_iata"] = iata.get("origin_iatas")

            if destination:
                session["destination_city"] = destination
                session["destination_iata"] = iata.get("destination_iatas")

            print("[Preprocess] Updated session:", session)
    else:
        print("[Preprocess] Using previous session")

    # =========================
    # STEP 1: LLM PARAM EXTRACT
    # =========================
    params = extract_flight_param(query, session)

    if not params:
        return {
            "status": "NEED_INFO",
            "message": "Mohon sebutkan tanggal keberangkatan.",
            "params": {}
        }

    print("[Params] From LLM:", params)

    # =========================
    # STEP 2: INJECT IATA
    # =========================
    if session.get("origin_iata"):
        params["departure_id"] = session["origin_iata"]

    if session.get("destination_iata"):
        params["arrival_id"] = session["destination_iata"]

    print("[Params] After inject:", params)

    # =========================
    # STEP 3: VALIDATION
    # =========================
    if not params.get("departure_id") or not params.get("arrival_id"):
        return {
            "status": "NEED_INFO",
            "message": "Mohon lengkapi kota asal dan tujuan.",
            "params": params
        }

    # =========================
    # STEP 4: AMBIGUITY
    # =========================
    if isinstance(params["departure_id"], list):
        return {
            "status": "AMBIGOUS",
            "message": "Pilih bandara asal:",
            "candidates": params["departure_id"],
            "field": "departure_id",
            "params": params
        }

    if isinstance(params["arrival_id"], list):
        return {
            "status": "AMBIGOUS",
            "message": "Pilih bandara tujuan:",
            "candidates": params["arrival_id"],
            "field": "arrival_id",
            "params": params
        }

    print("[FINAL PARAMS]", params)

    # =========================
    # STEP 5: API CALL
    # =========================
    result = search_flight_offers(
        origin=params["departure_id"],
        destination=params["arrival_id"],
        departure_date=params["outbound_date"],
        return_date=params.get("return_date"),
        adults=params.get("adults", 1),
        type = params.get("type"),
        travel_class=params.get("travel_class", "1"),
        currency=params.get("currency", "IDR")
    )

    if result["status"] != "OK":
        return result

    # =========================
    # STEP 6: BEAUTIFY
    # =========================
    beautified = beautify_flight_offerst(result=result)

    return {
        "status": "OK",
        "data": beautified,
        "params": params,
        "raw_offers": result.get("raw", [])
    }



# was 
# def format_duration(duration: str) -> str:
#     """
#     Convert PT1H45M -> 1H45M
#     """
#     if not duration:
#         return ""
#     return duration.replace("PT", "")


# def format_flight_options(offers: list) -> str:
#     """
#     Format multiple flight offers into readable text
#     """
#     if not offers:
#         return "No flights found."

#     output = []

#     for idx, offer in enumerate(offers, start=1):
#         go_segment = offer["itineraries"][0]["segments"][0]
#         return_segment = offer["itineraries"][1]["segments"][0]

#         output.append(f"\n===== OPTION {idx} =====")
#         output.append(
#             f"PRICE: {offer['price']['total']} {offer['price']['currency']}"
#         )
#         output.append(
#             f"Seats Available: {offer.get('numberOfBookableSeats', 'N/A')}"
#         )
#         output.append(
#             f"Go Duration: {format_duration(offer['itineraries'][0]['duration'])}"
#         )

#         output.append("\nGO FLIGHT:")
#         output.append(f"Flight: {go_segment['number']}")
#         output.append(f"Depart: {go_segment['departure']['at']}")
#         output.append(f"Arrive: {go_segment['arrival']['at']}")

#         output.append("\nRETURN FLIGHT:")
#         output.append(f"Flight: {return_segment['number']}")
#         output.append(f"Depart: {return_segment['departure']['at']}")
#         output.append(f"Arrive: {return_segment['arrival']['at']}")

#     return "\n".join(output)


# def flight_handler(query: dict) -> str:
#     """
#     Main handler for flight MCP
#     Expected query format:
#     {
#         "origin": "CGK",
#         "destination": "SIN",
#         "departure_date": "2026-03-06",
#         "return_date": "2026-03-20",
#         "adults": 1
#     }
#     """

#     offers = search_flight_offers(
#         origin=query.get("origin"),
#         destination=query.get("destination"),
#         departure_date=query.get("departure_date"),
#         return_date=query.get("return_date"),
#         adults=query.get("adults", 1),
#     )

#     if not offers:
#         return "No flight offers found."

#     # Limit to first 5 options
#     offers = offers[:5]

#     return format_flight_options(offers)