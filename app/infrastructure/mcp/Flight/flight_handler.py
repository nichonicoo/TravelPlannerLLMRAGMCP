from app.infrastructure.mcp.Flight.flight_search import search_flight_offers
from app.infrastructure.mcp.Flight.flight_beautifier import beautify_flight_offerst
from app.services.resolver import Resolver
import app.core.sessions as session


DESTINATION_ALIASES = {
    "canggu": "bali",
    "ubud": "bali",
    "kuta": "bali",
    "seminyak": "bali",
    "malioboro": "yogyakarta",
    "borobudur": "yogyakarta",
}

class FlightHandler:
    def __init__(self, client=None):
        self.client = client or search_flight_offers

    def normalize_city_name(name: str):
        if not name:
            return None
        key = name.lower().strip()
        return DESTINATION_ALIASES.get(key, key)


    async def __call__(self, params: dict) -> dict:
        """
        Handle flight search requests with standardized params dict.
        Returns status: OK, NEED_INFO, AMBIGUOUS, or ERROR.
        """
        # If params contains "query", we need to extract from it (backward compatibility)
        if "query" in params:
            # This is handled by the orchestrator passing query
            # For now, return NEED_INFO to indicate params need to be built
            return {
                "status": "NEED_INFO",
                "message": "Flight search requires specific parameters (departure_id, arrival_id, outbound_date)",
            }

        # Validate required params
        missing = []
        if not params.get("departure_id"):
            missing.append("kota asal")
        if not params.get("arrival_id"):
            missing.append("kota tujuan")
        if not params.get("outbound_date"):
            missing.append("tanggal")

        if missing:
            return {
                "status": "NEED_INFO",
                "message": f"Lengkapi: {', '.join(missing)}",
                "params": params
            }

        # Check for ambiguity (list of IATAs)
        if isinstance(params.get("departure_id"), list):
            return {
                "status": "AMBIGUOUS",
                "message": "Pilih bandara asal:",
                "candidates": params["departure_id"],
                "field": "departure_id",
                "params": params
            }

        if isinstance(params.get("arrival_id"), list):
            return {
                "status": "AMBIGUOUS",
                "message": "Pilih bandara tujuan:",
                "candidates": params["arrival_id"],
                "field": "arrival_id",
                "params": params
            }

        # Execute search
        result = self.client(
            origin=params["departure_id"],
            destination=params["arrival_id"],
            departure_date=params["outbound_date"],
            return_date=params.get("return_date"),
            adults=params.get("adults", 1),
            type=params.get("type"),
            travel_class=params.get("travel_class", "1"),
            currency=params.get("currency", "IDR")
        )

        if result["status"] != "OK":
            return result

        return {
            "status": "OK",
            "data": result,
            "params": params,
            "meta": {
                "raw_offers": result.get("raw", [])
            }
        }
