import serpapi
from app.core.settings import settings

api_key = settings.SERP_API_KEY
client = serpapi.Client(api_key=api_key)


def search_hotel(params: dict) -> dict:
    print('params: ', params)
    # Detail Mode
    if params.get("property_token"):
        search_params = {
            "engine": "google_hotels",
            "property_token": params["property_token"]
        }

    # Normal Search
    else:
        search_params = {
            "engine": "google_hotels",
            "q": f"hotel di {params['location']}",
            "gl": params.get("country", "id"),
            "hl": "id",
            "currency": params.get("currency", "IDR"),

            "check_in_date": params.get("check_in_date"),
            "check_out_date": params.get("check_out_date"),

            "adults": params.get("adults", 2),
            "children": params.get("children", 0),

            "sort_by": params.get("sort_by"),
            "min_price": params.get("min_price"),
            "max_price": params.get("max_price"),
        }
    try:
        response = client.search(search_params)

        return {
            "status": "OK",
            "properties": response.get("properties", []),
            "property": response.get("property", {})
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "message": str(e)
        }
