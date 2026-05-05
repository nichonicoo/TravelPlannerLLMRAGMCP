from LLM.orchestrator import reference_prev_locations
import app.core.sessions as session
from app.infrastructure.llm.base import LLMProvider
from app.infrastructure.rag.rag_pipeline import RAGEngine
from app.infrastructure.mcp.mcp_manager import MCPManager
from app.schemas.actions import ActionType
from app.services.resolver import Resolver
from app.services.extractors import Extractor
from app.services.response_formatter import ResponseFormatter


class Orchestrator:
    """Simple orchestrator that routes requests to MCP handlers.
    Validation and ambiguity resolution are handled within each MCP handler."""

    def __init__(self, llm: LLMProvider, rag: RAGEngine, mcp: MCPManager, resolver: Resolver, extractor: Extractor):
        self.llm = llm
        self.rag = rag
        self.mcp = mcp
        self.resolver = resolver
        self.extractor = extractor
        self.response_formatter = ResponseFormatter()

    async def handle(self, query: str) -> str:
        """Handle a user query by routing to the appropriate MCP handler."""
        s = session.get()
        session.tick()

        if s["state"]["awaiting_confirmation"]:
            resolution = self.resolver.resolve(query)

            if resolution.get("action") == "RETRY":
                result = self.mcp.execute(
                    resolution["intent"],
                    resolution["params"]
                )
                return self.resolver.process_result(
                    resolution["intent"],
                    result
                )
            elif resolution.get("action") == "ERROR":
                return resolution["message"]

        intent = await self._decision_routing(query)

        session.smart_reset_if_needed(intent, query)

        # TODO: implement reference_prev_locations
        # if reference_prev_locations:
        #     pass

        if intent == "LLM":
            result = {
                "action": ActionType.GENERATE_RESPONSE,
                "message": query
            }
        elif intent == "RAG":
            result = await self._handle_rag(query)
        elif intent == "WEATHER":
            raw_result = await self.mcp.execute(intent, {"query": query})
            result = self.resolver.process_result(intent, raw_result)
        elif intent == "FLIGHT":
            params = self._build_params(intent, query, s)
            raw_result = await self.mcp.execute(intent, params)
            result = self.resolver.process_result(intent, raw_result)
        elif intent == "HOTEL":
            params = self._build_params(intent, query, s)
            raw_result = await self.mcp.execute(intent, params)
            result = self.resolver.process_result(intent, raw_result)

        formatted = self.response_formatter.format(intent, result)

        final_response = await self._maybe_beautify(intent, formatted)

        return final_response

    async def _decision_routing(self, query: str) -> str:
        prompting = f"""Kamu adalah orchestrator Travel Assistant.
                    Klasifikasikan intent user ke salah satu:

                    - WEATHER  → cuaca, hujan, suhu, prakiraan, panas, dingin
                    - FLIGHT   → tiket pesawat, jadwal penerbangan, harga flight
                    - HOTEL   → hotel, penginapan, stay, resort, villa, tempat menginap
                    - RAG      → pertanyaan berbasis informasi/pengetahuan (contoh: sejarah tempat wisata, kapan dibangun, fakta destinasi, dll)
                    - LLM      → wisata, kuliner, rekomendasi tempat, obrolan umum

                    Balis SATU kata saja: WEATHER, FLIGHT, HOTEL, RAG, atau LLM.

                    Query: {query}"""

        answer = await self.llm.generate(prompting)
        if not answer:
            return "LLM"
        answer = answer.strip().upper()
        if answer not in ["WEATHER", "FLIGHT", "HOTEL", "RAG", "LLM"]:
            return "LLM"

        return answer

    def _build_params(self, intent: str, query: str, session_data: dict):
        builders = {
            "FLIGHT": self.extractor.build_flight_params,
            "HOTEL": self.extractor.build_hotel_params,
        }

        builder = builders.get(intent)

        if builder:
            return builder(query, session_data)

        return {"query": query}

    async def _handle_rag(self, query):
        print("[Router] RAG mode")

        context = self.rag.retrieve_context(query)

        if not context.strip():
            return {
                "action": ActionType.ERROR,
                "message": "RAG tidak mendapat hasil"
            }

        prompt = self.rag.build_prompt(context, query)
        result = await self.llm.generate(prompt)

        if "tidak tahu" in result.lower():
            return {
                "action": ActionType.ERROR,
                "message": "LLM tidak dapat menemukan informasi yang relevan dari rag"
            }

        return {
            "action": ActionType.GENERATE_RESPONSE,
            "message": result
        }

    async def _maybe_beautify(self, intent: str, formatted: str) -> str:
        # later implement if what intent, add prompt
        return await self.llm.generate(formatted)
