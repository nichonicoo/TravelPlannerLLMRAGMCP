from amadeus import Client, ResponseError, Location
from MCP.Flight import amadeus_auth
from LLM.orchestrator import add_carrier_names
import requests

search_flight_url = 'https://test.api.amadeus.com/v2/shopping/flight-offers'

def search_flight_offers(
    origin, 
    destination, 
    departure_date, 
    return_date = None, 
    adults = 1, 
    travel_class = None,
    currency = None
)-> dict :
    params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "returnDate": return_date,
            "adults": adults, 
            "currencyCode": currency,
            "max": 5
        }
    print('params: ', params)
    if return_date:
        params["returnDate"] = return_date
        
    token = amadeus_auth.get_token()
    if not token: 
        print("token not available")
            
    try:    
        # response = amadeus.shopping.flight_offers_search.get(**params)
        response = requests.get(
            search_flight_url,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        
        offers = data.get("data", [])
        if not offers: 
            print("offers is not available or not found")
            
        parsed = [parsing_offer(o) for o in offers]
        parsed = add_carrier_names(parsed)
        trip_type = "round_trip" if return_date else "one_way"
        
        print('return: ', offers)
        
        return {
            "status": "OK",
            "trip_type": trip_type,
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departure_date": departure_date,
            "return_date": return_date,
            "adults": adults,
            "offers": parsed,
            "raw": offers,   # disimpan untuk flight price check nanti
        }
        
    except requests.HTTPError as e:
        print(f"[Flight Search] HTTP Error: {e.response.status_code} - {e.response.text}")
        return {"status": "ERROR", "message": f"Amadeus error: {e.response.status_code}"}
    
    except Exception as e:
        print(f"[Flight Search] Error: {e}")
        return {"status": "ERROR", "message": str(e)}   
    
    
def parsing_offer(offer: dict) -> dict: 
    print('offer: ', offer)
    try: 
        price = offer.get("price", {})
        print('pricecuy: ', price)
        
        traveler_pricings = offer.get("travelerPricings", [])
        fare_details_list = traveler_pricings[0].get("fareDetailsBySegment", [] if traveler_pricings else [])
        
        fare_by_segment = {fd["segmentId"]: fd for fd in fare_details_list}    
            
        itineraries = []
    
        
        for itin in offer.get("itineraries", []):
            segments = []
            for seg in itin.get("segments", []):
                seg_id = seg.get("id", "")
                fare = fare_by_segment.get(seg_id, {})
                cabin = fare.get("cabin", "-")
                
                segments.append({
                "airline": seg.get("carrierCode", "-"),
                "airline_name": '-',
                    "flight_number": seg.get("carrierCode", "") + seg.get("number", ""),
                    "departure_airport": seg["departure"].get("iataCode", "-"),
                    "departure_time": seg["departure"].get("at", "-"),
                    "arrival_airport": seg["arrival"].get("iataCode", "-"),
                    "arrival_time": seg["arrival"].get("at", "-"),
                    "cabin": cabin,
                })
            itineraries.append({
                "duration": itin.get("duration", "-"),   # ex: PT2H10M
                "stops": len(itin.get("segments", [])) - 1,
                "segments": segments,
            })
    
        # bagasi 
        baggage = "-"
        
        first_fare = fare_details_list[0] if fare_details_list else {}
        included_bags = first_fare.get("includedCheckedBags", {})
        included_cabin = first_fare.get("includedCabinBags", {})
        
        if included_bags:
            qty = included_bags.get("quantity")
            weight = included_bags.get("weight")
            unit = included_bags.get("weightUnit", "KG")
            if weight:
                baggage = f"{weight} {unit}"
            elif qty:
                baggage = f"{qty} koper"
        elif included_cabin:
            qty = included_cabin.get("quantity")
            if qty:
                baggage = f"Kabin {qty} tas"
                
        first_cabin = fare_details_list[0].get("cabin", "-") if fare_details_list else "-"
                
        return {
            "offer_id": offer.get("id"),
            "price_idr": price.get("grandTotal", "-"),
            "currency": price.get("currency", "IDR"),
            "cabin": first_cabin,
            "baggage": baggage,
            "itineraries": itineraries,
            "validating_airline": offer.get("validatingAirlineCodes", ["-"])[0],
        }
        
    except Exception as e:
        print(f"[Flight Search] Parse error: {e}")
        return {"error": str(e), "raw": offer}