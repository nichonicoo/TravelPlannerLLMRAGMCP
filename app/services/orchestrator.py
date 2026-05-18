from typing import List
import app.core.sessions as session
from app.infrastructure.llm.base import LLMProvider
from app.infrastructure.rag.rag_pipeline import RAGEngine
from app.infrastructure.mcp.mcp_manager import MCPManager
from app.schemas.actions import ActionType
from app.schemas.message import Message
from app.services.promp_builder import PromptBuilder
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
        self.prompt_builder = PromptBuilder()

    async def handle(self, query: str) -> str:
        """Handle a user query by routing to the appropriate MCP handler."""
        s = session.get()
        session.tick()

        # TODO: Handle Confirmation Mode (Awaiting user confirmation)
        # if s["state"]["awaiting_confirmation"]:
        #     resolution = self.resolver.resolve(query)

        #     if resolution.get("action") == "RETRY":
        #         result = self.mcp.execute(
        #             resolution["intent"],
        #             resolution["params"]
        #         )
        #         return self.resolver.process_result(
        #             resolution["intent"],
        #             result
        #         )
        #     elif resolution.get("action") == "ERROR":
        #         return resolution["message"]

        # Info : Gas ganti intentnya kalau mau test fitur tertentu
        # intent = "LLM"
        intent = await self._decision_routing(query)
        session.smart_reset_if_needed(intent, query)

        # TODO: implement extract city
        # if reference_prev_locations:
        #     pass

        if intent == "LLM":
            result = {
                "action": ActionType.GENERATE_RESPONSE,
                "message": query
            }
        elif intent == "RAG":
            result = await self._handle_rag(query)
        elif intent in ["WEATHER", "FLIGHT", "HOTEL"]:
            params = self._build_params(intent, query, s)
            raw_result = await self.mcp.execute(intent, params)
            result = self.resolver.process_result(intent, raw_result)

        formatted = self.response_formatter.format(intent, result)

        final_response = await self._beautify_response(intent, result.get("action"), formatted, query)

        return final_response

    async def _decision_routing(self, query: str) -> str:
        messages: List[Message] = [
            {
                "role": "system",
                "content": (
                    "Kamu adalah orchestrator Travel Assistant.\n"
                    "Tugasmu adalah mengklasifikasikan intent user.\n"
                    "\n"
                    "Kategori:\n"
                    "- WEATHER → cuaca, suhu, prakiraan\n"
                    "- FLIGHT → tiket pesawat, jadwal, harga\n"
                    "- HOTEL → hotel, penginapan\n"
                    "- RAG → pertanyaan fakta (sejarah, lokasi, informasi umum)\n"
                    "- LLM → rekomendasi, wisata, kuliner, obrolan\n"
                    "\n"
                    "Jawab hanya dengan SATU kata:\n"
                    "WEATHER, FLIGHT, HOTEL, RAG, atau LLM.\n"
                    "Tanpa penjelasan."
                )
            },
            {
                "role": "user",
                "content": query
            }
        ]

        answer = await self.llm.generate(messages)

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
        
        messages = self.rag.build_prompt(context, query)
        result = await self.llm.generate(messages)
        
        if "tidak tahu" in result.lower():
            return {
                "action": ActionType.ERROR,
                "message": "LLM tidak dapat menemukan informasi yang relevan dari rag"
            }
        
        return {
            "action": ActionType.GENERATE_RESPONSE,
            "message": result
        }

    async def _beautify_response(self, intent: str, action: ActionType, result: str | dict, original_query: str) -> str:
        """Uses PromptBuilder to refine the final answer."""

        if action != ActionType.GENERATE_RESPONSE and isinstance(result, str):
            return result

        context = {
            "query": original_query,
            "data": result
        }

        messages = self.prompt_builder.build(intent, context)
        return await self.llm.generate(messages)
