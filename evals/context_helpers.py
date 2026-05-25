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
    """Slims down raw JSON data payloads from MCP servers to save downstream token context."""
    intent = intent.upper().strip()
    data_payload = result.get("data", {})
    
    if intent == "FLIGHT":
        offers = data_payload.get("offers", [])
        if not offers:
            return "No flight data available"

        simplified = [
            {
                "airline": flight.get("airline"),
                "flight_number": flight.get("flight_number"),
                "departure": flight.get("departure_airport", {}).get("time"),
                "arrival": flight.get("arrival_airport", {}).get("time"),
                "duration_minutes": flight.get("duration"),
                "price_idr": offer.get("price"),
            }
            for offer in offers[:10]
            if (flight := offer.get("flights", [{}])[0])
        ]
        return json.dumps(simplified, ensure_ascii=False)

    elif intent == "HOTEL":
        properties = data_payload.get("properties", [])
        if not properties:
            return "No hotel data available"

        simplified = [
            {
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
                "nearby": [p.get("name") for p in hotel.get("nearby_places", [])[:3]],
                "property_token": hotel.get("property_token")
            }
            for hotel in properties[:10]
        ]
        return json.dumps(simplified, ensure_ascii=False)

    return json.dumps(result, ensure_ascii=False, indent=2)
