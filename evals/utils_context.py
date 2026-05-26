import json
import pandas as pd


def normalize_date(value) -> str | None:
    """Safely normalizes input date values into %Y-%m-%d format using pandas."""
    if value is None or pd.isna(value):
        return None
    try:
        return pd.to_datetime(value).strftime("%Y-%m-%d")
    except Exception:
        return None


def build_mcp_params(intent: str, query: str, params: dict) -> dict:
    """Builds specific payload parameters based on target execution intents."""
    intent = intent.upper().strip()

    if intent == "WEATHER":
        return {"query": query}

    elif intent == "FLIGHT":
        return {
            "departure_id": params.get("departure_id"),
            "arrival_id": params.get("arrival_id"),
            "outbound_date": normalize_date(params.get("start_date")),
            "return_date": normalize_date(params.get("end_date")),
        }

    elif intent == "HOTEL":
        return {
            "location": params.get("location"),
            "check_in_date": normalize_date(params.get("start_date")),
            "check_out_date": normalize_date(params.get("end_date")),
        }

    return {"query": query}


def build_mcp_context(intent: str, result: dict) -> str:
    """
    Slims down raw JSON payloads from MCP servers while preserving
    enough structured information for downstream prompting.
    """

    intent = intent.upper().strip()
    data_payload = result.get("data", {})

    # ==================================================
    # FLIGHT
    # ==================================================
    if intent == "FLIGHT":

        offers = data_payload.get("offers", [])
        departure_date = data_payload.get("departure_date")
        return_date = data_payload.get("return_date")

        if not offers:
            return "No flight data available"

        simplified = []

        for offer in offers[:10]:

            flight = offer.get("flights", [{}])[0]

            dep_airport = flight.get("departure_airport", {})
            arr_airport = flight.get("arrival_airport", {})

            simplified.append({
                "type": flight.get("type"),
                "airplane": flight.get("airplane"),
                "airline": flight.get("airline"),
                "travel_class": flight.get("travel_class"),
                "legroom": flight.get("legroom"),
                "extensions": flight["extensions", []],
                "flight_number": flight.get("flight_number"),
                "departure": flight["departure_airport"]["time"],
                "arrival": flight["arrival_airport"]["time"],
                "duration_minutes": flight.get("duration"),
                "price_idr": offer.get("price"),
                "departure_airport_name": dep_airport.get("name"),
                "departure_airport_id": dep_airport.get("id"),
                "departure_time": dep_airport.get("time"),
                "arrival_airport_name": arr_airport.get("name"),
                "arrival_airport_id": arr_airport.get("id"),
                "arrival_time": arr_airport.get("time"),
                "departure_date": departure_date,
                "return_date": return_date
            })

        final_response = {
            "search": {
                "departure_date": departure_date,
                "return_date": return_date
            },
            "flights": simplified
        }

        return json.dumps(final_response, ensure_ascii=False)

    # ==================================================
    # HOTEL
    # ==================================================
    elif intent == "HOTEL":
        properties = data_payload.get("properties", [])
        search_params = data_payload.get("search_parameters", {})

        if not properties:
            return "No hotel data available"

        check_in_date = search_params.get("check_in_date")
        check_out_date = search_params.get("check_out_date")

        simplified = []

        for hotel in properties[:10]:

            simplified.append({
                "name": hotel.get("name"),
                "hotel_class": hotel.get("extracted_hotel_class"),
                "price_per_night": hotel.get("rate_per_night", {}).get("extracted_lowest"),
                "total_price": hotel.get("total_rate", {}).get("extracted_lowest"),
                "rating": hotel.get("overall_rating"),
                "reviews": hotel.get("reviews"),
                "location_rating": hotel.get("location_rating"),
                "amenities": hotel.get("amenities", [])[:5],
                "check_in": hotel.get("check_in_time"),
                "check_out": hotel.get("check_out_time"),
                "nearby": [
                    p.get("name")
                    for p in hotel.get("nearby_places", [])[:3]
                ],
                "property_token": hotel.get("property_token")
            })

        final_response = {
            "search": {
                "check_in_date": check_in_date,
                "check_out_date": check_out_date
            },
            "hotels": simplified
        }

        return json.dumps(final_response, ensure_ascii=False)

    # ==================================================
    # DEFAULT
    # ==================================================
    return json.dumps(result, ensure_ascii=False, indent=2)
