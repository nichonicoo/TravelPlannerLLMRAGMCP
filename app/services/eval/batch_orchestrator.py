import json
import time
import pandas as pd
from app.infrastructure.llm.base import LLMProvider
from app.infrastructure.rag.rag_pipeline import RAGEngine
from app.infrastructure.mcp.mcp_manager import MCPManager

from app.services.extractors import Extractor
from app.services.resolver import Resolver

from app.services.eval.prompts import (
    LLM_PROMPT,
    RAG_PROMPT,
    MCP_PROMPT
)


class BatchOrchestrator:
    """
    Simplified orchestrator for evaluation.

    Responsibilities:
    - route intent
    - inject context/tool results
    - call LLM

    No memory.
    No beautification.
    No autonomous reasoning.
    """

    def __init__(
        self,
        llm: LLMProvider,
        rag: RAGEngine,
        mcp: MCPManager,
        resolver: Resolver,
    ):
        self.llm = llm
        self.rag = rag
        self.mcp = mcp
        self.resolver = resolver
        self.extractor = Extractor(llm)

    # ==================================================
    # MAIN ENTRY
    # ==================================================
    async def handle(
        self,
        intent: str,
        query: str,
        row: dict
    ) -> dict:

        start = time.perf_counter()

        try:

            intent = intent.upper().strip()

            if intent == "LLM":
                result = await self._handle_llm(query)

            elif intent == "RAG":
                result = await self._handle_rag(query)

            elif intent in ["FLIGHT", "HOTEL", "WEATHER"]:
                result = await self._handle_mcp(
                    intent=intent,
                    query=query,
                    row=row
                )

            else:
                result = {
                    "status": "ERROR",
                    "response": "Unsupported intent"
                }

        except Exception as e:

            result = {
                "status": "ERROR",
                "response": str(e)
            }

        latency = time.perf_counter() - start

        result["latency"] = round(latency, 3)
        result["intent"] = intent
        result["query"] = query

        return result

    # ==================================================
    # MESSAGE BUILDER
    # ==================================================
    def _build_messages(
        self,
        system_prompt: str,
        query: str
    ) -> list[dict]:

        return [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": query
            }
        ]

    # ==================================================
    # LLM
    # ==================================================
    async def _handle_llm(
        self,
        query: str
    ) -> dict:

        messages = self._build_messages(
            system_prompt=LLM_PROMPT,
            query=query
        )

        response = await self.llm.generate(messages)

        return {
            "status": "SUCCESS",
            "response": response,
            "context": None,
            "tool_result": None,
        }

    # ==================================================
    # RAG
    # ==================================================
    async def _handle_rag(
        self,
        query: str
    ) -> dict:

        context = self.rag.retrieve_context(query)

        if not context.strip():

            return {
                "status": "NOT_FOUND",
                "response": "Informasi tidak ditemukan.",
                "context": context,
                "tool_result": None,
            }

        system_prompt = RAG_PROMPT.format(
            context=context
        )

        messages = self._build_messages(
            system_prompt=system_prompt,
            query=query
        )

        response = await self.llm.generate(messages)

        return {
            "status": "SUCCESS",
            "response": response,
            "context": context,
            "tool_result": None,
        }

    # ==================================================
    # MCP
    # ==================================================
    async def _handle_mcp(
        self,
        intent: str,
        query: str,
        row: dict
    ) -> dict:
        params = self._build_mcp_params(
            intent=intent,
            query=query,
            row=row
        )

        raw_result = await self.mcp.execute(
            intent,
            params
        )

        tool_result = self._build_mcp_context(
            intent,
            raw_result
        )

        system_prompt = MCP_PROMPT.format(
            tool_result=tool_result
        )

        messages = self._build_messages(
            system_prompt=system_prompt,
            query=query
        )

        response = await self.llm.generate(messages)

        return {
            "status": raw_result.get("status", "ERROR"),
            "response": response,
            "context": None,
        }

    # ==================================================
    # MCP RESULT FORMATTER
    # ==================================================
    def _build_mcp_context(
        self,
        intent: str,
        result: dict
    ) -> str:
        if intent == "FLIGHT":
            offers = result.get("data", {}).get("offers", [])
            if not offers:
                return "No flight data available"

            simplified = []

            for offer in offers[:10]:
                flight = offer["flights"][0]

                simplified.append({
                    "airline": flight.get("airline"),
                    "flight_number": flight.get("flight_number"),
                    "departure": flight["departure_airport"]["time"],
                    "arrival": flight["arrival_airport"]["time"],
                    "duration_minutes": flight.get("duration"),
                    "price_idr": offer.get("price"),
                })

            return json.dumps(
                simplified,
                ensure_ascii=False
            )
        elif intent == "HOTEL":
            properties = result.get("data", {}).get("properties", [])
            if not properties:
                return "No hotel data available"

            simplified = []

            for hotel in properties[:10]:
                simplified.append({
                    "name": hotel.get("name"),
                    "hotel_class": hotel.get("extracted_hotel_class"),
                    "price_per_night": hotel.get("rate_per_night", {})
                        .get("extracted_lowest"),
                    "total_price": hotel.get("total_rate", {})
                        .get("extracted_lowest"),
                    "rating": hotel.get("overall_rating"),
                    "reviews": hotel.get("reviews"),
                    "location_rating": hotel.get("location_rating"),
                    "amenities": hotel.get("amenities", [])[:5],
                    "check_in": hotel.get("check_in_time"),
                    "check_out": hotel.get("check_out_time"),
                    "nearby": [
                        p.get("name")
                        for p in hotel.get(
                                "nearby_places",
                                []
                            )[:3]
                        ],
                    "property_token": hotel.get("property_token")
                })

            return json.dumps(
                simplified,
                ensure_ascii=False
            )

        return json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )

    # ==================================================
    # MCP PARAM BUILDERS
    # ==================================================
    def _build_mcp_params(
        self,
        intent: str,
        query: str,
        row: dict
    ) -> dict:

        if intent == "WEATHER":
            return {
                "query": query
            }

        elif intent == "FLIGHT":
            return {
                "departure_id": row.get("departure_id"),
                "arrival_id": row.get("arrival_id"),
                "outbound_date": self._normalize_date(row.get("start_date")),
                "return_date": self._normalize_date(row.get("end_date")),
            }

        elif intent == "HOTEL":
            return {
                "location": row.get("location"),
                "check_in_date": self._normalize_date(row.get("start_date")),
                "check_out_date": self._normalize_date(row.get("end_date")),
            }

        return {
            "query": query
        }

    def _normalize_date(self, value):
        if value is None:
            return None

        if pd.isna(value):
            return None

        try:
            return pd.to_datetime(value).strftime(
                "%Y-%m-%d"
            )

        except Exception:
            return None
