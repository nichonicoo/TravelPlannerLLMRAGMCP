# from MCP.Flight import amadeus_auth
# from LLM.orchestrator import add_carrier_names
import serpapi
import requests
import os

api_key = os.getenv("SERP_API_KEY")
client = serpapi.Client(api_key= "8962b25df7d68e5f681dee47d5b60b686262e4c1a1836faa8bf218076b0e09ec")

data_tok = {
  "search_metadata": {
    "id": "69c3e9e4ad9ecf3a7e4b092d",
    "status": "Success",
    "json_endpoint": "https://serpapi.com/searches/IbUJBq4_AcHZGrhOPEq3Mw/69c3e9e4ad9ecf3a7e4b092d.json",
    "created_at": "2026-03-25 13:57:56 UTC",
    "processed_at": "2026-03-25 13:57:56 UTC",
    "google_flights_url": "https://www.google.com/travel/flights?hl=en&gl=us&curr=IDR&tfs=CBwQAhoeEgoyMDI2LTAzLTI2agcIARIDQ0dLcgcIARIDTUxHGh4SCjIwMjYtMDQtMDFqBwgBEgNNTEdyBwgBEgNDR0tAAUgBcAGYAQE&tfu=EgIIAQ",
    "raw_html_file": "https://serpapi.com/searches/IbUJBq4_AcHZGrhOPEq3Mw/69c3e9e4ad9ecf3a7e4b092d.html",
    "prettify_html_file": "https://serpapi.com/searches/IbUJBq4_AcHZGrhOPEq3Mw/69c3e9e4ad9ecf3a7e4b092d.prettify",
    "total_time_taken": 1.29
  },
  "search_parameters": {
    "engine": "google_flights",
    "hl": "en",
    "gl": "us",
    "departure_id": "CGK",
    "arrival_id": "MLG",
    "outbound_date": "2026-03-26",
    "return_date": "2026-04-01",
    "adults": 1,
    "currency": "IDR"
  },
  "other_flights": [
    {
      "flights": [
        {
          "departure_airport": {
            "name": "Soekarno–Hatta International Airport",
            "id": "CGK",
            "time": "2026-03-26 09:35"
          },
          "arrival_airport": {
            "name": "Abdul Rachman Saleh Airport",
            "id": "MLG",
            "time": "2026-03-26 10:55"
          },
          "duration": 80,
          "airplane": "Airbus A320",
          "airline": "Citilink Indonesia",
          "airline_logo": "https://www.gstatic.com/flights/airline_logos/70px/QG.png",
          "travel_class": "Economy",
          "flight_number": "QG 752",
          "legroom": "28 in",
          "extensions": [
            "Below average legroom (28 in)",
            "Carbon emissions estimate: 76 kg"
          ]
        }
      ],
      "total_duration": 80,
      "carbon_emissions": {
        "this_flight": 77000,
        "typical_for_this_route": 80000,
        "difference_percent": -4
      },
      "price": 2141582,
      "type": "Round trip",
      "airline_logo": "https://www.gstatic.com/flights/airline_logos/70px/QG.png",
      "departure_token": "WyJDalJJVWpWV2NuZDNSbEJFT1dOQlEyWnZkbEZDUnkwdExTMHRMUzB0TFc5clpHMHlNVUZCUVVGQlIyNUVObVZWU0ZscFltOUJFZ1ZSUnpjMU1ob01DSTdiZ2dFUUFCb0RTVVJTT0J4d21tTT0iLFtbIkNHSyIsIjIwMjYtMDMtMjYiLCJNTEciLG51bGwsIlFHIiwiNzUyIl1dXQ=="
    },
    {
      "flights": [
        {
          "departure_airport": {
            "name": "Soekarno–Hatta International Airport",
            "id": "CGK",
            "time": "2026-03-26 08:30"
          },
          "arrival_airport": {
            "name": "Abdul Rachman Saleh Airport",
            "id": "MLG",
            "time": "2026-03-26 10:10"
          },
          "duration": 100,
          "airplane": "Airbus A320",
          "airline": "Batik Air",
          "airline_logo": "https://www.gstatic.com/flights/airline_logos/70px/ID.png",
          "travel_class": "Economy",
          "flight_number": "ID 6566",
          "legroom": "32 in",
          "extensions": [
            "Above average legroom (32 in)",
            "In-seat USB outlet",
            "Stream media to your device",
            "Carbon emissions estimate: 82 kg"
          ]
        }
      ],
      "total_duration": 100,
      "carbon_emissions": {
        "this_flight": 83000,
        "typical_for_this_route": 80000,
        "difference_percent": 4
      },
      "price": 2168104,
      "type": "Round trip",
      "airline_logo": "https://www.gstatic.com/flights/airline_logos/70px/ID.png",
      "departure_token": "WyJDalJJVWpWV2NuZDNSbEJFT1dOQlEyWnZkbEZDUnkwdExTMHRMUzB0TFc5clpHMHlNVUZCUVVGQlIyNUVObVZWU0ZscFltOUJFZ1pKUkRZMU5qWWFEQWlvcW9RQkVBQWFBMGxFVWpnY2NMaGsiLFtbIkNHSyIsIjIwMjYtMDMtMjYiLCJNTEciLG51bGwsIklEIiwiNjU2NiJdXV0="
    },
    {
      "flights": [
        {
          "departure_airport": {
            "name": "Soekarno–Hatta International Airport",
            "id": "CGK",
            "time": "2026-03-26 12:55"
          },
          "arrival_airport": {
            "name": "Abdul Rachman Saleh Airport",
            "id": "MLG",
            "time": "2026-03-26 14:35"
          },
          "duration": 100,
          "airplane": "Airbus A320",
          "airline": "Batik Air",
          "airline_logo": "https://www.gstatic.com/flights/airline_logos/70px/ID.png",
          "travel_class": "Economy",
          "flight_number": "ID 6564",
          "legroom": "32 in",
          "extensions": [
            "Above average legroom (32 in)",
            "In-seat USB outlet",
            "Stream media to your device",
            "Carbon emissions estimate: 82 kg"
          ]
        }
      ],
      "total_duration": 100,
      "carbon_emissions": {
        "this_flight": 83000,
        "typical_for_this_route": 80000,
        "difference_percent": 4
      },
      "price": 2287104,
      "type": "Round trip",
      "airline_logo": "https://www.gstatic.com/flights/airline_logos/70px/ID.png",
      "departure_token": "WyJDalJJVWpWV2NuZDNSbEJFT1dOQlEyWnZkbEZDUnkwdExTMHRMUzB0TFc5clpHMHlNVUZCUVVGQlIyNUVObVZWU0ZscFltOUJFZ1pKUkRZMU5qUWFEQWlBeklzQkVBQWFBMGxFVWpnY2NQbHAiLFtbIkNHSyIsIjIwMjYtMDMtMjYiLCJNTEciLG51bGwsIklEIiwiNjU2NCJdXV0="
    }
  ],
  "price_insights": {
    "lowest_price": 2141582,
    "price_level": "low",
    "typical_price_range": [
      2300000,
      2950000
    ],
    "price_history": [
      [
        1769187600,
        2612780
      ],
      [
        1769274000,
        2612780
      ],
      [
        1769360400,
        2612780
      ],
      [
        1769446800,
        2612780
      ],
      [
        1769533200,
        2612780
      ],
      [
        1769619600,
        2612780
      ],
      [
        1769706000,
        2612780
      ],
      [
        1769792400,
        2612780
      ],
      [
        1769878800,
        2678280
      ],
      [
        1769965200,
        2678280
      ],
      [
        1770051600,
        2678280
      ],
      [
        1770138000,
        2678280
      ],
      [
        1770224400,
        2678280
      ],
      [
        1770310800,
        2678280
      ],
      [
        1770397200,
        2678280
      ],
      [
        1770483600,
        2678280
      ],
      [
        1770570000,
        2678280
      ],
      [
        1770656400,
        2553480
      ],
      [
        1770742800,
        2553480
      ],
      [
        1770829200,
        2398020
      ],
      [
        1770915600,
        2292000
      ],
      [
        1771002000,
        2292000
      ],
      [
        1771088400,
        2292000
      ],
      [
        1771174800,
        2292000
      ],
      [
        1771261200,
        2387520
      ],
      [
        1771347600,
        2292000
      ],
      [
        1771434000,
        2292000
      ],
      [
        1771520400,
        2292000
      ],
      [
        1771606800,
        2292000
      ],
      [
        1771693200,
        2352000
      ],
      [
        1771779600,
        2352000
      ],
      [
        1771866000,
        2352000
      ],
      [
        1771952400,
        2292000
      ],
      [
        1772038800,
        2292000
      ],
      [
        1772125200,
        2292000
      ],
      [
        1772211600,
        2292000
      ],
      [
        1772298000,
        2358600
      ],
      [
        1772384400,
        2358600
      ],
      [
        1772470800,
        2344978
      ],
      [
        1772557200,
        2344978
      ],
      [
        1772643600,
        2344978
      ],
      [
        1772730000,
        2278378
      ],
      [
        1772816400,
        2278378
      ],
      [
        1772902800,
        2278378
      ],
      [
        1772989200,
        2278378
      ],
      [
        1773075600,
        2344978
      ],
      [
        1773162000,
        2344978
      ],
      [
        1773248400,
        2278378
      ],
      [
        1773334800,
        2278378
      ],
      [
        1773421200,
        2278378
      ],
      [
        1773507600,
        2233000
      ],
      [
        1773594000,
        2233000
      ],
      [
        1773680400,
        2233000
      ],
      [
        1773766800,
        2233000
      ],
      [
        1773853200,
        2196478
      ],
      [
        1773939600,
        2196478
      ],
      [
        1774026000,
        2196478
      ],
      [
        1774112400,
        2146478
      ],
      [
        1774198800,
        2146478
      ],
      [
        1774285200,
        2146478
      ],
      [
        1774371600,
        2141582
      ]
    ]
  },
  "airports": [
    {
      "departure": [
        {
          "airport": {
            "id": "CGK",
            "name": "Soekarno–Hatta International Airport"
          },
          "city": "Jakarta",
          "country": "Indonesia",
          "country_code": "ID",
          "image": "https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcTziuEPHQ7bf7hJJD8qV-IxAa31KflOd_hVrPVZPo7IM-G_mLBOu-T4lstilfKaXt5_4E24RHxseoESHA",
          "thumbnail": "https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcRdBGVcPnKq5Tzb4cqDoKQnMTA2FVAXAsk__oLDwNi2IKKlexVolcd5D-O344J-YOp0mAA-kVCXi9840lFFCcCjQdPO28Qnnke4-XeX4Cg"
        }
      ],
      "arrival": [
        {
          "airport": {
            "id": "MLG",
            "name": "Abdul Rachman Saleh Airport"
          },
          "city": "Malang",
          "country": "Indonesia",
          "country_code": "ID",
          "image": "https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcRA1zdNvJnz52FqRi7OCy3iC8eUP3BzovxZLQmXjbn7GxPLQodThlGTeQEOPvCdt8chrO9PKxo2aROuaA",
          "thumbnail": "https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcR6aXVJtcMm-u3GzCAXoHirVbQuxHaO3U3LybxkMnmS0iBJcapJ1b4rztSyedCNdWBYv1eV85k6X0nOmNybcEz3CGGKUTn-doyYqfQec90"
        }
      ]
    },
    {
      "departure": [
        {
          "airport": {
            "id": "MLG",
            "name": "Abdul Rachman Saleh Airport"
          },
          "city": "Malang",
          "country": "Indonesia",
          "country_code": "ID",
          "image": "https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcRA1zdNvJnz52FqRi7OCy3iC8eUP3BzovxZLQmXjbn7GxPLQodThlGTeQEOPvCdt8chrO9PKxo2aROuaA",
          "thumbnail": "https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcR6aXVJtcMm-u3GzCAXoHirVbQuxHaO3U3LybxkMnmS0iBJcapJ1b4rztSyedCNdWBYv1eV85k6X0nOmNybcEz3CGGKUTn-doyYqfQec90"
        }
      ],
      "arrival": [
        {
          "airport": {
            "id": "CGK",
            "name": "Soekarno–Hatta International Airport"
          },
          "city": "Jakarta",
          "country": "Indonesia",
          "country_code": "ID",
          "image": "https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcTziuEPHQ7bf7hJJD8qV-IxAa31KflOd_hVrPVZPo7IM-G_mLBOu-T4lstilfKaXt5_4E24RHxseoESHA",
          "thumbnail": "https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcRdBGVcPnKq5Tzb4cqDoKQnMTA2FVAXAsk__oLDwNi2IKKlexVolcd5D-O344J-YOp0mAA-kVCXi9840lFFCcCjQdPO28Qnnke4-XeX4Cg"
        }
      ]
    }
  ]
}

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
        
        # print('return: ', parsed)
        
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

    
    # print('offer: ', offer)
    # # try: 
    # #     price = offer.get("flights", {})
    # #     print('pricecuy: ', price)
        
    # #     traveler_pricings = offer.get("travelerPricings", [])
    # #     fare_details_list = traveler_pricings[0].get("fareDetailsBySegment", [] if traveler_pricings else [])
        
    # #     fare_by_segment = {fd["segmentId"]: fd for fd in fare_details_list}    
            
    # #     itineraries = []
    
        
    # #     for itin in offer.get("itineraries", []):
    # #         segments = []
    # #         for seg in itin.get("segments", []):
    # #             seg_id = seg.get("id", "")
    # #             fare = fare_by_segment.get(seg_id, {})
    # #             cabin = fare.get("cabin", "-")
                
    # #             segments.append({
    # #             "airline": seg.get("carrierCode", "-"),
    # #             "airline_name": '-',
    # #                 "flight_number": seg.get("carrierCode", "") + seg.get("number", ""),
    # #                 "departure_airport": seg["departure"].get("iataCode", "-"),
    # #                 "departure_time": seg["departure"].get("at", "-"),
    # #                 "arrival_airport": seg["arrival"].get("iataCode", "-"),
    # #                 "arrival_time": seg["arrival"].get("at", "-"),
    # #                 "cabin": cabin,
    # #             })
    # #         itineraries.append({
    # #             "duration": itin.get("duration", "-"),   # ex: PT2H10M
    # #             "stops": len(itin.get("segments", [])) - 1,
    # #             "segments": segments,
    # #         })
    
    # #     # bagasi 
    # #     baggage = "-"
        
    # #     first_fare = fare_details_list[0] if fare_details_list else {}
    # #     included_bags = first_fare.get("includedCheckedBags", {})
    # #     included_cabin = first_fare.get("includedCabinBags", {})
        
    # #     if included_bags:
    # #         qty = included_bags.get("quantity")
    # #         weight = included_bags.get("weight")
    # #         unit = included_bags.get("weightUnit", "KG")
    # #         if weight:
    # #             baggage = f"{weight} {unit}"
    # #         elif qty:
    # #             baggage = f"{qty} koper"
    # #     elif included_cabin:
    # #         qty = included_cabin.get("quantity")
    # #         if qty:
    # #             baggage = f"Kabin {qty} tas"
                
    # #     first_cabin = fare_details_list[0].get("cabin", "-") if fare_details_list else "-"
                
    # #     return {
    # #         "offer_id": offer.get("id"),
    # #         "price_idr": price.get("grandTotal", "-"),
    # #         "currency": price.get("currency", "IDR"),
    # #         "cabin": first_cabin,
    # #         "baggage": baggage,
    # #         "itineraries": itineraries,
    # #         "validating_airline": offer.get("validatingAirlineCodes", ["-"])[0],
    # #     }
        
    # except Exception as e:
    #     print(f"[Flight Search] Parse error: {e}")
    #     return {"error": str(e), "raw": offer}
    
    
# search_flight_offers(
#     'CGK',
#     'SIN',
#     '1',
#     '2026-03-27',
#     '2026-03-29',
#     '1',
#     None, 
#     None, 
#     None, 
#     None, 
#     '1',
#     'IDR'
# )

# search_flight_offers(
#     origin = 'CGK', 
#     destination = 'SIN', 
#     type = '1', 
#     departure_date = '2026-03-27', 
#     return_date = '2026-03-29',
#     adults = 1, 
#     children = None, 
#     infants_in_seat = None, 
#     infants_on_lap = None,
#     travel_class = '1',
#     currency ='IDR'
# )

parsing_offer(data_tok)