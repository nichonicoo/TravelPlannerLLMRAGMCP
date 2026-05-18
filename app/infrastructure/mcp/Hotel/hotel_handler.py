from app.infrastructure.mcp.Hotel.hotel_search import search_hotel


class HotelHandler:
    def __init__(self, client=None):
        self.client = client or search_hotel

    async def __call__(self, params: dict) -> dict:
        """
        Handle hotel search requests with standardized params dict.
        Returns status: OK, NEED_INFO, AMBIGUOUS, or ERROR.
        """
        # DETAIL MODE
        if params.get("property_token"):
            result = self.client({
                "property_token": params["property_token"]
            })

            if result["status"] != "OK":
                return {
                    "status": "ERROR",
                    "error": "HOTEL_DETAIL_FAILED",
                    "data": result
                }

            return {
                "status": "OK",
                "data": result
            }

        # missing_fields = []

        # if not params.get("location"):
        #     missing_fields.append("location")

        # if not params.get("check_in_date"):
        #     missing_fields.append("check_in_date")

        # if not params.get("check_out_date"):
        #     missing_fields.append("check_out_date")

        # if missing_fields:
        #     return {
        #         "status": "NEED_INFO",
        #         "data": {
        #             "missing_fields": missing_fields
        #         },
        #         "error": "MISSING_PARAMETERS"
        #     }

        if not params.get("location"):
            return {
                "status": "NEED_INFO",
                "data": {
                    "missing_fields": ["location"]
                },
                "error": "MISSING_LOCATION"
            }

        result = self.client(params)

        if result["status"] != "OK":
            return {
                "status": "ERROR",
                "error": "HOTEL_SEARCH_FAILED",
                "data": result
            }

        return {
            "status": "OK",
            "data": result
        }
