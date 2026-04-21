# from MCP.Flight import amadeus_auth
# from LLM.orchestrator import add_carrier_names
import serpapi
import requests
import os
api_key = os.getenv("SERP_API_KEY")
client = serpapi.Client(api_key=api_key)

def search_flight_offers(
    origin, 
    destination, 
    type, 
    departure_date, 
    return_date = None,
    adults = 1, 
    children = None, 
    infants_in_seat = None, 
    infants_on_lap = None,
    travel_class = None,
    currency = None
)-> dict :
    params = {
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination, 
            "type": type, 
            "outbound_date": departure_date, 
            "return_date": return_date, 
            "travel_class": travel_class, 
            "adults": adults, 
            "children": children, 
            "infants_in_seat": infants_in_seat,
            "infants_on_lap": infants_on_lap, 
            "currency": currency
        }
    print('params: ', params)
    
    if return_date:
        params["return_date"] = return_date
        params["type"] = "1"
        
    if not return_date: 
        params["return_date"] = None
        params["type"] = "2"
        
    try:    
        response = client.search(params)
        print('data raw: ', response)
        
        offers = response.get("best_flights", []) or response.get("other_flights", [])
        if not offers: 
            print("offers is not available or not found")
            
        parsed = parsing_offer(response)
        
        return {
            "status": "OK",
            "trip_type": 'test',
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departure_date": departure_date,
            "return_date": return_date,
            "adults": adults,
            "offers": parsed,
            "raw": offers,   # disimpan untuk flight price check nanti
        }
        
    except serpapi.HTTPError as e:
        if e.status_code == 401: # Invalid API key
            print(e.error) # "Invalid API key. Your API key should be here: https://serpapi.com/manage-api-key"
        elif e.status_code == 400: # Missing required parameter
            print(e.error)
        elif e.status_code == 429: # Exceeds the hourly throughput limit OR account run out of searches
            print(e.error)
        
    except serpapi.TimeoutError as e:
        # Handle timeout
        print(f"The request timed out: {e}")
    
    
def parsing_offer(offer: dict) -> dict: 
  offers = offer.get("best_flights") or offer.get("other_flights") or []
  return offers