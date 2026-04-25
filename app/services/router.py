from app.infrastructure.llm.base import LLMProvider
from app.infrastructure.rag.rag_pipeline import RAGEngine
from app.infrastructure.mcp.mcp_manager import MCPManager
import app.core.sessions as session
from app.services.orchestrator import decision_routing, reference_prev_locations
from MCP.mcp_mock import run_mcp
from app.services.resolver import Resolver
from app.services.prompts.weather_prompts import WEATHER_BEAUTIFIER_PROMPT


class Router:
    def __init__(self, llm: LLMProvider, rag: RAGEngine, mcp_manager: MCPManager, resolver: Resolver):
        self.llm = llm
        self.rag = rag
        self.mcp_manager = mcp_manager
        self.resolver = resolver

    def route_request(self, query: str) -> str:
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

                result = self.mcp_manager.execute(query=selected, intent="WEATHER",
                                                  force_context=True)

                return self._handle_weather_result(result)

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

                # Safety: ensure no list remains
                if isinstance(params.get("departure_id"), list):
                    params["departure_id"] = params["departure_id"][0]
                if isinstance(params.get("arrival_id"), list):
                    params["arrival_id"] = params["arrival_id"][0]

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

        # 2 classified the intent
        action = decision_routing(query, self.llm)
        print(f"[Router] Action: {action}")

        # reset if topik bkn non travel
        session.smart_reset_if_needed(action, query)

        # 3. cek kata2 referensi kaya :dimana disitu kesana

        if reference_prev_locations(query, self.llm) and session.has_city():
            session.touch_city()
            print(
                f"[Router] Konteks dirujuk → pakai kota: {s['last_city_name']}")

            if action == "WEATHER":
                result = self.mcp_manager.execute(
                    query=s["last_city_name"],
                    intent="WEATHER",
                    force_context=True,
                )
                return self._handle_weather_result(result)

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
                return self._handle_flight_result(result)

        # 4. normal routing

        if action == "WEATHER":
            print('weather now')
            result = self.mcp_manager.execute(query=query, intent="WEATHER")
            return self._handle_weather_result(result)

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
                return self._handle_flight_result(result)

            result = run_mcp(query=query, intent="FLIGHT", session=s)
            return self._handle_flight_result(result)

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

            context = self.rag.retrieve_context(query)

            if not context.strip():
                return self.llm.generate(query)

            prompt = self.rag.build_prompt(context, query)
            answer = self.llm.generate(prompt)

            if "tidak tahu" in answer.lower():
                return self.llm.generate(query)

            return answer

        # LLM — jawab langsung, tapi tetap ekstrak kota kalau ada
        answer = self.llm.generate(query)

        # Simpan kota ke session kalau ada di query
        from LLM.orchestrator import extract_city
        print('extract city now')
        city = extract_city(query)
        print('city extracted: ', city)
        if city:
            iata = self.resolver.city_to_iata(city)
            print('city to iata extracted: ', city)
            session.update_city(cityname=city, iata=iata)
            print(f"[Session] Kota diekstrak dari LLM turn: {city} ({iata})")

        return answer

    def _handle_weather_result(self, result: dict) -> str:
        status = result.get("status")

        if status == "OK":
            session.update_city(
                cityname=result.get("location_name", session.get()[
                                    "last_city_name"]),
                adm4=result.get("adm4"),
            )
            session.clear_confirmation()
            prompt = WEATHER_BEAUTIFIER_PROMPT.format(
                raw_data=result.get("data"))
            return self.llm.generate(prompt)

        if status == "AMBIGUOUS":
            session.set_confirmation("WEATHER", result.get("candidates", []))

            # new
            session.get()["pending_query"] = result.get("original_query")
            candidates = result.get("candidates", [])
            candidates_str = "\n".join(
                [f"{i+1}. {c}" for i, c in enumerate(candidates)])

            # candidates_str = "\n- ".join(session.get()["candidates"])
            return f"Lokasi tidak dikenali secara pasti. Maksudnya yang mana?\n- {candidates_str}"

        if status == "NOT_FOUND":
            return "Maaf, lokasi tidak dikenali. Sebutkan nama kota yang lebih spesifik."

        return "Maaf, terjadi kesalahan saat mengambil data cuaca."

    def _handle_hotel_result(self, result: dict) -> str:
        return "ok"

    def _handle_flight_result(self, result: dict) -> str:
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
                f"{i+1}. {self.resolver.get_airport_full_name(c)}"
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
