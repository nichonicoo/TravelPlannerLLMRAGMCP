from app.infrastructure.mcp.Hotel.hotel_search import search_hotel


class HotelHandler:
    def __init__(self, client=None):
        self.client = client or search_hotel

    async def __call__(self, params: dict) -> dict:
        """
        Handle hotel search requests with standardized params dict.
        Returns status: OK, NEED_INFO, AMBIGUOUS, or ERROR.
        """
        # If params contains "query", we need to extract from it (backward compatibility)
        if "query" in params:
            # This is handled by the orchestrator passing query
            # For now, return NEED_INFO to indicate params need to be built
            return {
                "status": "NEED_INFO",
                "message": "Hotel search requires specific parameters (location, check_in, check_out)",
            }

        # DETAIL MODE
        if params.get("property_token"):
            result = self.client({
                "property_token": params["property_token"]
            })

            if result["status"] != "OK":
                return {
                    "status": "ERROR",
                    "message": result
                }

            return {
                "status": "OK",
                "data": result
            }

        if not params.get("location"):
            return {
                "status": "NEED_INFO",
                "message": "Mau cari hotel di kota mana?",
            }

        result = self.client(params)

        if result["status"] != "OK":
            return {
                "status": "ERROR",
                "message": result
            }

        return {
            "status": "OK",
            "data": result
        }
