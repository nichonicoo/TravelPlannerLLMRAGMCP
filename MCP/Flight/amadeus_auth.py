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