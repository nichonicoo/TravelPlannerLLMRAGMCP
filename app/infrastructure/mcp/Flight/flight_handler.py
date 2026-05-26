from app.infrastructure.mcp.Flight.flight_search import search_flight_offers


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

    def normalize_city_name(self, name: str):
        if not name:
            return None

        key = name.lower().strip()
        return DESTINATION_ALIASES.get(key, key)

    async def __call__(self, params: dict) -> dict:
        """
        Handle flight search requests with standardized params dict.
        Returns status: OK, NEED_INFO, AMBIGUOUS, or ERROR.
        """

        # =========================
        # PARAM VALIDATION
        # =========================

        missing_fields = []

        if not params.get("departure_id"):
            missing_fields.append("departure_id")

        if not params.get("arrival_id"):
            missing_fields.append("arrival_id")

        if not params.get("outbound_date"):
            missing_fields.append("outbound_date")

        if missing_fields:
            return {
                "status": "NEED_INFO",
                "data": {
                    "missing_fields": missing_fields,
                    "params": params
                },
                "error": "Missing required fields"
            }

        # =========================
        # AMBIGUOUS AIRPORTS
        # =========================

        if isinstance(params.get("departure_id"), list):
            return {
                "status": "AMBIGUOUS",
                "data": {
                    "field": "departure_id",
                    "candidates": params["departure_id"],
                    "params": params
                },
                "error": "AMBIGUOUS_DEPARTURE_AIRPORT"
            }

        if isinstance(params.get("arrival_id"), list):
            return {
                "status": "AMBIGUOUS",
                "data": {
                    "field": "arrival_id",
                    "candidates": params["arrival_id"],
                    "params": params
                },
                "error": "AMBIGUOUS_ARRIVAL_AIRPORT"
            }

        # =========================
        # EXECUTE SEARCH
        # =========================

        result = self.client(
            origin=params["departure_id"],
            destination=params["arrival_id"],
            departure_date=params.get("outbound_date"),
            return_date=params.get("return_date"),
            adults=params.get("adults", 1),
            travel_class=params.get("travel_class", "1"),
            currency=params.get("currency", "IDR")
        )

        # =========================
        # MCP FAILURE
        # =========================

        if result.get("status") != "OK":
            return {
                "status": result.get("status", "ERROR"),
                "error": result.get("error", "FLIGHT_SEARCH_FAILED"),
                "data": {
                    "params": params
                }
            }

        # =========================
        # SUCCESS
        # =========================

        return {
            "status": "OK",
            "data": {
                "offers": result.get("offers", []),
                "departure_date": params.get("outbound_date"),
                "return_date": params.get("return_date"),
                "params": params
            },
            "meta": {
                "raw_offers": result.get("raw", [])
            }
        }
