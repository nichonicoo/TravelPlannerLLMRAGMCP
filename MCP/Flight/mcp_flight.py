from amadeus import Client, ResponseError, Location
import os, json, requests, time
from dotenv import load_dotenv

load_dotenv()

_cache = {
    "token": None,
    "expires_in": 0,
}
amadeus_auth_link = 'https://test.api.amadeus.com/v1/security/oauth2/token'

# amadeus = Client(
#     client_id = os.getenv("AMADEUS_CLIENT_ID"),
#     client_secret = os.getenv("AMADEUS_CLIENT_KEY")
# )

# to get token 
def get_token() -> str | None:
    if _cache["token"] and time.time() < _cache["expires_in"]:
        print('Amadus Auth using cachce token')
        return _cache["token"]
    
    client_id = os.getenv("AMADEUS_CLIENT_ID"),
    client_secret = os.getenv("AMADEUS_CLIENT_KEY")
    
    if not client_id or not client_secret:
        print("client id or client secret is not valid or null")
        return None
    
    try: 
        r = requests.post(
            amadeus_auth_link,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        
        r.raise_for_status()
        data = r.json()
        
        _cache["token"] = data["access_token"]
        _cache["expires_in"] = time.time() +  data["expires_in"] - 60
        
        print(f"'success get token. expires in {data['expires_in']}s.")
        
        return _cache["token"]
    
    except requests.HTTPError as e: 
        print(f"[Amadeus Auth] HTTP Error: {e.response.status_code} - {e.response.text}")
        return None

    except Exception as e:
        print(f"[Amadeus Auth] Error: {e}")
        return None

def search_flight_offers(
    origin, 
    destination, 
    departure_date, 
    return_date = None, 
    adults = 1, 
    currency = "IDR" 
):
    try: 
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "returnDate": return_date,
            "adults": adults, 
            "currencyCode": currency,
            "max": 5
        }
        # print('params: ', params)
        if return_date:
            params["returnDate"] = return_date
            
        response = amadeus.shopping.flight_offers_search.get(**params)
        
        return response.data
    except ResponseError as error: 
        print("Search Error:", error)
        return None

def price_flight_offer(flight_offer_object, acc_token):
    url = "https://test.api.amadeus.com/v1/shopping/flight-offers/pricing"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {acc_token}"
    }
    
    payload = {
        "data": {
            "type": "flight-offers-pricing",
            "flightOffers": [flight_offer_object]
        }
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print("Success!")
            return response.json()
        else:
            print(f"Error {response.status_code}:")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"Connection Error: {e}")
        return None

def scrub_offer_for_pricing(raw_offer):
    # Field yang HARUS ada untuk Pricing
    clean_offer = {
        "type": raw_offer["type"],
        "id": raw_offer["id"],
        "source": raw_offer["source"],
        "instantTicketingRequired": raw_offer["instantTicketingRequired"],
        "lastTicketingDate": raw_offer["lastTicketingDate"],
        "itineraries": [],
        "price": raw_offer["price"],
        "pricingOptions": raw_offer["pricingOptions"],
        "validatingAirlineCodes": raw_offer["validatingAirlineCodes"],
        "travelerPricings": raw_offer["travelerPricings"]
    }

    # Scrub Itineraries
    for itinerary in raw_offer["itineraries"]:
        clean_itinerary = {"duration": itinerary["duration"], "segments": []}
        for segment in itinerary["segments"]:
            clean_segment = {
                "departure": segment["departure"],
                "arrival": segment["arrival"],
                "carrierCode": segment["carrierCode"],
                "number": segment["number"],
                "aircraft": segment["aircraft"],
                "duration": segment["duration"],
                "id": segment["id"], # ID ini penting untuk mapping
                "numberOfStops": segment["numberOfStops"]
            }
            clean_itinerary["segments"].append(clean_segment)
        clean_offer["itineraries"].append(clean_itinerary)

    return clean_offer

def format_duration(duration):
    duration = duration.replace("PT", "")
    hours = duration.split("H")[0]
    minutes = duration.split("H")[1].replace("M", "")
    return f"{hours}h {minutes}m"
    
if __name__ == "__main__":
    
    get_token()

    # offers = search_flight_offers(
    #     origin="CGK",
    #     destination="SIN",
    #     departure_date="2026-03-06",
    #     return_date="2026-03-20",
    #     adults= 1,
    #     currency= "USD"
    # )
    
    # print('acc token:', amadeus.access_token.access_token)

    # if offers: 
    #     print('offers: ')
    #     print(offers)
    #     print("==========================")
    #     for idx, offer in enumerate(offers, start=1):

    #         # clean_payload = scrub_offer_for_pricing(offer)

    #         go = offer["itineraries"][0]["segments"][0]
    #         ret = offer["itineraries"][1]["segments"][0]

    #         print(f"\n===== OPTION {idx} =====")

    #         print("ID:", offer["id"])
    #         print("Price:", offer["price"]["total"], offer["price"]["currency"])
    #         print("Seats:", offer["numberOfBookableSeats"])

    #         print("\nGO:")
    #         print("Flight:", go["number"])
    #         print("Depart:", go["departure"]["at"])
    #         print("Arrive:", go["arrival"]["at"])

    #         print("\nRETURN:")
    #         print("Flight:", ret["number"])
    #         print("Depart:", ret["departure"]["at"])
    #         print("Arrive:", ret["arrival"]["at"])
            
    #     # disini lanjut LLM, tergantung user mau pilih jam berapa gitu ya 
        
    #     payload = scrub_offer_for_pricing(offers[0])
    #     pricing_result = price_flight_offer(payload, amadeus.access_token.access_token)

    #     if pricing_result:
    #         print("PRICED RESULT:")
    #         # print(pricing_result)


